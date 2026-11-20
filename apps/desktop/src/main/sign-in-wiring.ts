import { join, resolve } from "node:path";

import { app, ipcMain, net, shell } from "electron";

import { CHANNELS, type Account } from "@shared/bridge";

import { DeviceAuth, SIGN_IN_WAIT_MS, SignInFailed } from "./auth/device-auth";
import { SessionVault } from "./auth/session-vault";
import type { DesktopConfig } from "./config";
import { keychain } from "./store/keychain";
import { LocalStore } from "./store/local-store";
import { sendToWindows } from "./windows";

/** The app's own link scheme, which the browser opens when sign-in is allowed. */
const SCHEME = "jalada";

/** Finds a jalada:// link among the arguments Windows and Linux start a second copy with. */
function linkIn(argv: string[]): string | undefined {
  return argv.find((argument) => argument.startsWith(`${SCHEME}://`));
}

/**
 * Makes this app the one that opens jalada:// links. Run from source, Electron itself is
 * the program, so it has to be told which app to start with it (Electron's own advice).
 */
function registerScheme(): void {
  const fromSource = (process as { defaultApp?: boolean }).defaultApp === true;
  const entry = process.argv[1];
  if (fromSource && entry) {
    app.setAsDefaultProtocolClient(SCHEME, process.execPath, [resolve(entry)]);
  } else {
    app.setAsDefaultProtocolClient(SCHEME);
  }
}

/** A message for the window: the reason when sign-in refused, plain words otherwise. */
function why(error: unknown): string {
  return error instanceof SignInFailed
    ? error.message
    : "The server could not be reached to finish signing in. Try again.";
}

/**
 * Sign-in through the browser (decision 0029): registers the jalada:// link, answers the
 * window's account questions, and finishes sign-in when the link comes back. Tells
 * `accountChanged` whenever someone signs in or out.
 */
export function wireSignIn(
  config: DesktopConfig,
  store: LocalStore,
  accountChanged: (account: Account | null) => void,
): DeviceAuth {
  registerScheme();
  const auth = new DeviceAuth({
    ...config,
    vault: new SessionVault(
      join(app.getPath("userData"), "session.bin"),
      keychain,
    ),
    // Only ever the web app's own sign-in page, built by DeviceAuth from the config.
    openInBrowser: async (url) => {
      if (new URL(url).origin === config.webOrigin)
        await shell.openExternal(url);
    },
    fetch: (url, init) => net.fetch(url, init),
    changed: (account) => {
      sendToWindows(CHANNELS.accountChanged, account);
      accountChanged(account);
    },
    forgetRecords: (accountId) => store.forget(accountId),
  });

  const finish = async (link: string): Promise<void> => {
    try {
      await auth.finish(link);
    } catch (error) {
      sendToWindows(CHANNELS.signInFailed, why(error));
    }
  };
  // The window stops waiting when the browser takes too long, instead of waiting forever.
  let giveUp: NodeJS.Timeout | undefined;
  const start = async (): Promise<void> => {
    clearTimeout(giveUp);
    await auth.start();
    giveUp = setTimeout(() => {
      // Signed in meanwhile: nothing to give up. A cancel clears this timer itself.
      if (auth.current()) return;
      auth.cancel();
      sendToWindows(
        CHANNELS.signInFailed,
        "Sign-in took too long. Start again when you are ready.",
      );
      // Still nobody signed in: says so, which ends the window's wait.
      sendToWindows(CHANNELS.accountChanged, null);
    }, SIGN_IN_WAIT_MS);
  };
  // macOS hands the link to the running app; Windows and Linux start a second copy with it.
  app.on("open-url", (event, link) => {
    event.preventDefault();
    void finish(link);
  });
  app.on("second-instance", (_event, argv) => {
    const link = linkIn(argv);
    if (link) void finish(link);
  });

  ipcMain.handle(CHANNELS.account, () => auth.current());
  ipcMain.handle(CHANNELS.signIn, () => start());
  ipcMain.handle(CHANNELS.cancelSignIn, () => {
    clearTimeout(giveUp);
    auth.cancel();
  });
  ipcMain.handle(CHANNELS.pasteSignInLink, (_event, link: unknown) =>
    typeof link === "string" ? finish(link) : undefined,
  );
  ipcMain.handle(CHANNELS.signOut, () => auth.signOut());
  return auth;
}

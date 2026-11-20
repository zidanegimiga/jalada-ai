import { join } from "node:path";

import { app, ipcMain, net, shell } from "electron";

import { CHANNELS, type Account } from "@shared/bridge";

import { DeviceAuth } from "./auth/device-auth";
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
 * Sign-in through the browser (decision 0029): registers the jalada:// link, answers the
 * window's account questions, and finishes sign-in when the link comes back. Tells
 * `accountChanged` whenever someone signs in or out.
 */
export function wireSignIn(
  config: DesktopConfig,
  store: LocalStore,
  accountChanged: (account: Account | null) => void,
): DeviceAuth {
  app.setAsDefaultProtocolClient(SCHEME);
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

  const finish = (link: string) => {
    auth.finish(link).catch((error: Error) => {
      sendToWindows(CHANNELS.signInFailed, error.message);
    });
  };
  // macOS hands the link to the running app; Windows and Linux start a second copy with it.
  app.on("open-url", (event, link) => {
    event.preventDefault();
    finish(link);
  });
  app.on("second-instance", (_event, argv) => {
    const link = linkIn(argv);
    if (link) finish(link);
  });

  ipcMain.handle(CHANNELS.account, () => auth.current());
  ipcMain.handle(CHANNELS.signIn, () => auth.start());
  ipcMain.handle(CHANNELS.signOut, () => auth.signOut());
  return auth;
}

import { join } from "node:path";
import { pathToFileURL } from "node:url";

import { app, BrowserWindow, ipcMain, session } from "electron";

import { CHANNELS } from "@shared/bridge";

import { applySecurity } from "./apply-security";
import { loadConfig } from "./config";
import { current, watchConnection } from "./connection";
import { startLedger, wireLedger } from "./ledger-wiring";
import { windowPreferences } from "./security";
import { wireSignIn } from "./sign-in-wiring";
import { keychain } from "./store/keychain";
import { LocalStore } from "./store/local-store";

const config = loadConfig(process.env);
const page = join(__dirname, "../renderer/index.html");
const appEntry = pathToFileURL(page).href;

/** One app at a time, so two copies never write to the same local database. */
if (!app.requestSingleInstanceLock()) app.quit();

// Each person's encrypted records, under the app's own data folder.
const store = new LocalStore(join(app.getPath("userData"), "local"), keychain);
// The ledger and sign-in each need the other, so the ledger asks for sign-in lazily.
const ledger = wireLedger(config, store, () => auth);
// Before the app is ready: macOS can hand over a sign-in link while it starts.
const auth = wireSignIn(config, store, (account) => ledger.switchTo(account));

function createWindow(): BrowserWindow {
  const window = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 380,
    minHeight: 560,
    title: "Jalada AI",
    backgroundColor: "#f4f3e8",
    // Shown once the first screen has painted, so it never opens blank.
    show: false,
    webPreferences: windowPreferences(join(__dirname, "../preload/index.cjs")),
  });
  window.once("ready-to-show", () => window.show());
  void window.loadFile(page);
  return window;
}

ipcMain.handle(CHANNELS.appInfo, () => ({
  version: app.getVersion(),
  apiOrigin: config.apiOrigin,
}));
ipcMain.handle(CHANNELS.connection, () => current());

void app.whenReady().then(() => {
  applySecurity(session.defaultSession, config, appEntry);
  const backOnline = startLedger(ledger, auth);
  const window = createWindow();
  watchConnection((connection) => {
    window.webContents.send(CHANNELS.connectionChanged, connection);
    backOnline(connection);
  });
  app.on("second-instance", () => {
    if (window.isMinimized()) window.restore();
    window.focus();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

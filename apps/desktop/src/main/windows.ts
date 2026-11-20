import { BrowserWindow } from "electron";

/** Sends one message to every open window, such as a change of account or ledger. */
export function sendToWindows(channel: string, value: unknown): void {
  for (const window of BrowserWindow.getAllWindows()) {
    window.webContents.send(channel, value);
  }
}

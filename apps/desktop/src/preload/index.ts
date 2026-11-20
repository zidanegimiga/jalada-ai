import { contextBridge, ipcRenderer, type IpcRendererEvent } from "electron";

import { CHANNELS, type JaladaBridge } from "@shared/bridge";

/** Listens on one channel until the returned function is called. */
function listen<T>(channel: string, changed: (value: T) => void): () => void {
  const listener = (_event: IpcRendererEvent, value: T) => changed(value);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
}

/**
 * The only door between the window and the main process (decision 0029). Each call is a
 * named question with a known answer; the window cannot send arbitrary messages.
 */
const bridge: JaladaBridge = {
  app: { info: () => ipcRenderer.invoke(CHANNELS.appInfo) },
  connection: {
    current: () => ipcRenderer.invoke(CHANNELS.connection),
    onChange: (changed) => listen(CHANNELS.connectionChanged, changed),
  },
  account: {
    current: () => ipcRenderer.invoke(CHANNELS.account),
    signIn: () => ipcRenderer.invoke(CHANNELS.signIn),
    signOut: () => ipcRenderer.invoke(CHANNELS.signOut),
    onChange: (changed) => listen(CHANNELS.accountChanged, changed),
    onFailed: (failed) => listen(CHANNELS.signInFailed, failed),
  },
  ledger: {
    list: (limit, offset) =>
      ipcRenderer.invoke(CHANNELS.ledgerList, limit, offset),
    status: () => ipcRenderer.invoke(CHANNELS.ledgerStatus),
    refresh: () => ipcRenderer.invoke(CHANNELS.ledgerRefresh),
    onChange: (changed) => listen(CHANNELS.ledgerChanged, changed),
  },
};

contextBridge.exposeInMainWorld("jalada", bridge);

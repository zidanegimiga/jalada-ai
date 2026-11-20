import { contextBridge, ipcRenderer } from "electron";

import { CHANNELS, type Connection, type JaladaBridge } from "@shared/bridge";

/**
 * The only door between the window and the main process (decision 0029). Each call is a
 * named question with a known answer; the window cannot send arbitrary messages.
 */
const bridge: JaladaBridge = {
  app: { info: () => ipcRenderer.invoke(CHANNELS.appInfo) },
  connection: {
    current: () => ipcRenderer.invoke(CHANNELS.connection),
    onChange: (changed) => {
      const listener = (_event: unknown, connection: Connection) =>
        changed(connection);
      ipcRenderer.on(CHANNELS.connectionChanged, listener);
      return () =>
        ipcRenderer.removeListener(CHANNELS.connectionChanged, listener);
    },
  },
};

contextBridge.exposeInMainWorld("jalada", bridge);

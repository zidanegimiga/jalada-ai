/**
 * Everything the window may ask of the main process, and nothing more (decision 0029).
 * The preload script puts an object of this shape on `window.jalada`; the window never
 * reaches Node.js, the file system or the network itself.
 */
export type Connection = "online" | "offline";

export type AppInfo = {
  version: string;
  /** The server the app syncs with, shown so people know where their records go. */
  apiOrigin: string;
};

export type JaladaBridge = {
  app: { info: () => Promise<AppInfo> };
  connection: {
    current: () => Promise<Connection>;
    /** Calls back whenever the connection changes. Returns a function that stops it. */
    onChange: (changed: (connection: Connection) => void) => () => void;
  };
};

/** The names of the messages between the bridge and the main process. */
export const CHANNELS = {
  appInfo: "app:info",
  connection: "connection:current",
  connectionChanged: "connection:changed",
} as const;

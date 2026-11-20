import type { WebPreferences } from "electron";

/**
 * The rules every window and request follows (decision 0029). They are plain functions so
 * they can be tested without starting Electron; `apply-security.ts` wires them in.
 */

/** Window settings: the page gets no Node.js, runs sandboxed, and sees only the bridge. */
export function windowPreferences(preload: string): WebPreferences {
  return {
    preload,
    sandbox: true,
    contextIsolation: true,
    nodeIntegration: false,
    nodeIntegrationInWorker: false,
    webSecurity: true,
    allowRunningInsecureContent: false,
    webviewTag: false,
    spellcheck: false,
    devTools: true,
  };
}

/**
 * Whether a request may leave the app: its own files, and the API, and nothing else. Every
 * other address, including fonts, analytics and other websites, is cancelled.
 */
export function isAllowedRequest(address: string, apiOrigin: string): boolean {
  let url: URL;
  try {
    url = new URL(address);
  } catch {
    return false;
  }
  if (url.protocol === "file:" || url.protocol === "devtools:") return true;
  if (url.protocol === "data:" || url.protocol === "blob:") return true;
  return url.origin === apiOrigin;
}

/** Only the app's own page may be shown; links elsewhere open in the system browser. */
export function isOwnPage(address: string, appEntry: string): boolean {
  try {
    const url = new URL(address);
    const entry = new URL(appEntry);
    return url.protocol === entry.protocol && url.pathname === entry.pathname;
  } catch {
    return false;
  }
}

/**
 * Links the app may hand to the system browser: pages of the Jalada AI web app, such as the
 * privacy notice, and nothing else. Never another website, a file or a command, so neither
 * the app nor anything shown in it can send the person somewhere they did not choose.
 */
export function mayOpenOutside(address: string, webOrigin: string): boolean {
  try {
    return new URL(address).origin === webOrigin;
  } catch {
    return false;
  }
}

/**
 * The page's Content Security Policy: only its own scripts and styles, and no network at
 * all. The window asks the main process for data through the bridge; only the main process
 * talks to the API. Also written into index.html, since pages loaded from files get no
 * response headers.
 */
export function contentSecurityPolicy(): string {
  return [
    "default-src 'none'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'none'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
  ].join("; ");
}

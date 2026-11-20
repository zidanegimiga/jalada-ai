import { app, shell, type Session } from "electron";

import {
  contentSecurityPolicy,
  isAllowedRequest,
  isOwnPage,
  mayOpenOutside,
} from "./security";
import type { DesktopConfig } from "./config";

/** The site a blocked request was for, never its full address, which may carry data. */
function originOf(address: string): string {
  try {
    return new URL(address).origin;
  } catch {
    return "an address that could not be read";
  }
}

/**
 * Wires the rules in `security.ts` into Electron: cancels outgoing requests that are not to
 * the app or the API, sets the page's Content Security Policy, refuses every permission,
 * and keeps every window on the app's own page.
 */
export function applySecurity(
  session: Session,
  { apiOrigin, webOrigin }: DesktopConfig,
  appEntry: string,
) {
  session.webRequest.onBeforeRequest((details, respond) => {
    const allowed = isAllowedRequest(details.url, apiOrigin);
    if (!allowed) console.warn(`Blocked a request to ${originOf(details.url)}`);
    respond({ cancel: !allowed });
  });

  session.webRequest.onHeadersReceived((details, respond) => {
    respond({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [contentSecurityPolicy()],
      },
    });
  });

  // Camera, microphone, location, notifications and the rest: never granted to the page.
  session.setPermissionRequestHandler((_contents, _permission, decide) =>
    decide(false),
  );
  session.setPermissionCheckHandler(() => false);

  app.on("web-contents-created", (_event, contents) => {
    contents.on("will-navigate", (event, address) => {
      if (isOwnPage(address, appEntry)) return;
      event.preventDefault();
      if (mayOpenOutside(address, webOrigin)) void shell.openExternal(address);
    });
    contents.on("will-attach-webview", (event) => event.preventDefault());
    contents.setWindowOpenHandler(({ url }) => {
      if (mayOpenOutside(url, webOrigin)) void shell.openExternal(url);
      return { action: "deny" };
    });
  });
}

/** What the desktop app sends to the browser, and the link that takes the answer back. */

// The SHA-256 of the app's secret, unpadded base64url (RFC 7636).
const CHALLENGE = /^[A-Za-z0-9_-]{43}$/;
// The app's random value, sent back untouched so it can tell the answer is to its own request.
const STATE = /^[A-Za-z0-9_-]{16,64}$/;

export type DesktopRequest = { challenge: string; state: string };

/** The desktop app's request from the page address, or null when it is not one. */
export function readDesktopRequest(params: {
  challenge?: string | string[];
  state?: string | string[];
}): DesktopRequest | null {
  const { challenge, state } = params;
  if (typeof challenge !== "string" || typeof state !== "string") return null;
  if (!CHALLENGE.test(challenge) || !STATE.test(state)) return null;
  return { challenge, state };
}

/** The link that opens the desktop app with its one-time code. */
export function backToApp(code: string, state: string): string {
  const query = new URLSearchParams({ code, state });
  return `jalada://signed-in?${query}`;
}

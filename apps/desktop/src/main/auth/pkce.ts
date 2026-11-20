import { createHash, randomBytes } from "node:crypto";

/**
 * The values for one sign-in through the browser (RFC 7636, decision 0029). The verifier
 * never leaves this computer; the browser only sees its hash, the challenge. The state comes
 * back with the answer, so the app can tell it is the answer to its own request.
 */
export type SignInRequest = {
  verifier: string;
  challenge: string;
  state: string;
};

export function newSignInRequest(): SignInRequest {
  const verifier = randomBytes(48).toString("base64url");
  return {
    verifier,
    challenge: createHash("sha256").update(verifier).digest("base64url"),
    state: randomBytes(24).toString("base64url"),
  };
}

export type SignInAnswer = { code: string; state: string };

/** The code and state from a `jalada://signed-in` link, or null for anything else. */
export function readSignInLink(link: string): SignInAnswer | null {
  let url: URL;
  try {
    url = new URL(link);
  } catch {
    return null;
  }
  if (url.protocol !== "jalada:" || url.hostname !== "signed-in") return null;
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (!code || !state || code.length > 100 || state.length > 64) return null;
  return { code, state };
}

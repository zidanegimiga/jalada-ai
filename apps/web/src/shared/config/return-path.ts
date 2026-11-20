/** The name of the address parameter that says where to go after signing in. */
export const RETURN_PARAM = "next";

/**
 * Where to go after signing in: the page the person was sent away from, if it is a page of
 * this site. Anything else, such as another website ("//evil.example") or a script, becomes
 * home, so a link cannot use sign-in to send someone elsewhere.
 */
export function safeReturnPath(raw: string | null | undefined): string {
  if (
    !raw ||
    !raw.startsWith("/") ||
    raw.startsWith("//") ||
    raw.includes("\\")
  ) {
    return "/";
  }
  try {
    const url = new URL(raw, "https://jalada.invalid");
    if (url.origin !== "https://jalada.invalid") return "/";
    return `${url.pathname}${url.search}`;
  } catch {
    return "/";
  }
}

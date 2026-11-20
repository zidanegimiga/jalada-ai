import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/shared/config/session-cookie";

const PUBLIC_PATHS = ["/signin", "/signup", "/privacy", "/welcome", "/offline"];

/**
 * Sends visitors without a session cookie to sign in, except at the front door, where they
 * see the landing page instead. The API still checks every request.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const signedIn = request.cookies.has(SESSION_COOKIE);
  if (PUBLIC_PATHS.includes(pathname) || signedIn) return NextResponse.next();
  if (pathname === "/")
    return NextResponse.rewrite(new URL("/welcome", request.url));
  return NextResponse.redirect(new URL("/signin", request.url));
}

export const config = {
  // Everything except API calls, Next.js assets and files with an extension.
  matcher: ["/((?!v1/|_next/|.*\\.).*)"],
};

import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/features/auth/session";

const PUBLIC_PATHS = ["/signin", "/signup"];

/** Sends visitors without a session cookie to sign in. The API still checks every request. */
export function proxy(request: NextRequest) {
  const isPublic = PUBLIC_PATHS.includes(request.nextUrl.pathname);
  if (isPublic || request.cookies.has(SESSION_COOKIE)) return NextResponse.next();
  return NextResponse.redirect(new URL("/signin", request.url));
}

export const config = {
  // Everything except API calls, Next.js assets and files with an extension.
  matcher: ["/((?!v1/|_next/|.*\\.).*)"],
};

"use client";

import { useSyncExternalStore } from "react";

import { RETURN_PARAM, safeReturnPath } from "@/shared/config/return-path";

// The address does not change while the page is open, so there is nothing to subscribe to.
const unchanging = () => () => {};

function returnPathHere(): string | null {
  const raw = new URLSearchParams(window.location.search).get(RETURN_PARAM);
  const safe = safeReturnPath(raw);
  return safe === "/" ? null : safe;
}

/**
 * The page to go back to after signing in, from this page's own address, or null. Read in
 * the browser, so the sign-in pages themselves stay static.
 */
export function useReturnPath(): string | null {
  return useSyncExternalStore(unchanging, returnPathHere, () => null);
}

/**
 * The same link, carrying the page to go back to. Moving between sign-in and sign-up, or
 * out to Google, must not lose it, or the person ends up at home instead.
 */
export function withReturnPath(
  href: string,
  returnPath: string | null,
): string {
  if (!returnPath) return href;
  const url = new URL(href, "https://jalada.invalid");
  url.searchParams.set(RETURN_PARAM, returnPath);
  return `${url.pathname}${url.search}`;
}

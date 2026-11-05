"use client";

import { useSearchParams } from "next/navigation";

const MESSAGES: Record<string, string> = {
  google_failed: "Google sign-in did not work. Try again, or use your email.",
  google_unavailable: "Google sign-in is not available right now. Use your email instead.",
};

/** Shows why the user was sent back to sign in, from the `error` query parameter. */
export function SignInNotice() {
  const message = MESSAGES[useSearchParams().get("error") ?? ""];
  if (!message) return null;
  return (
    <p role="alert" className="rounded-xl bg-secondary px-4 py-3 text-secondary-foreground">
      {message}
    </p>
  );
}

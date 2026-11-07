"use client";

import { useSearchParams } from "next/navigation";

const MESSAGES: Record<string, string> = {
  password_removed:
    "You are now signed in with Google. This account's password was removed, and everyone else using it was signed out, because nobody had confirmed the email address. Use Google to sign in from now on.",
};

/** Explains a change to the account after sign-in, from the `notice` query parameter. */
export function AccountNotice() {
  const message = MESSAGES[useSearchParams().get("notice") ?? ""];
  if (!message) return null;
  return (
    <p
      role="status"
      className="rounded-3xl bg-secondary px-5 py-4 text-secondary-foreground"
    >
      {message}
    </p>
  );
}

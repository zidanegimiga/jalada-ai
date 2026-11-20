"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/shared/components/Button";

/**
 * After the person allows sign-in: the browser has been asked to open the desktop app with
 * the link. Some browsers and systems will not open it, so the link is also shown to copy
 * into the app. It works once, for two minutes, and only with the app's own secret.
 */
export function HandBack({ link }: { link: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="flex flex-col gap-4 rounded-card bg-card p-card">
      <p role="status" className="text-lead">
        Opening the Jalada AI desktop app. Once it says you are signed in, you
        can close this tab.
      </p>
      <p className="text-muted-foreground">
        If the app did not open, copy this sign-in link and paste it into the
        app. It works once, for two minutes.
      </p>
      <label htmlFor="desktop-link" className="sr-only">
        Sign-in link for the desktop app
      </label>
      <input
        id="desktop-link"
        readOnly
        value={link}
        onFocus={(event) => event.currentTarget.select()}
        className="min-h-tap w-full rounded-control border border-input bg-background px-3 font-mono text-small"
      />
      <Button size="lg" variant="secondary" onClick={() => void copy()}>
        {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
        {copied ? "Copied" : "Copy the sign-in link"}
      </Button>
    </section>
  );
}

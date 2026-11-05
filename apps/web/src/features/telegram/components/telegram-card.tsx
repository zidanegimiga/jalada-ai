"use client";

import { Send } from "lucide-react";
import { useState } from "react";

import { Button, buttonVariants } from "@/components/ui/button";

type LinkCode = { code: string; bot_link: string | null };

/** Links a Telegram chat, so receipts can be sent from there. Hidden when the bot is off. */
export function TelegramCard({
  available,
  linked,
}: {
  available: boolean;
  linked: boolean;
}) {
  const [code, setCode] = useState<LinkCode | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!available) return null;
  if (linked) {
    return (
      <p className="text-muted-foreground">
        Telegram is linked. Send receipts to the bot any time.
      </p>
    );
  }

  async function getCode() {
    setError(null);
    const response = await fetch("/v1/telegram/link-code", { method: "POST" });
    if (response.ok) setCode((await response.json()) as LinkCode);
    else setError("Could not get a code. Try again.");
  }

  return (
    <section
      aria-labelledby="telegram-heading"
      className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-5"
    >
      <h2 id="telegram-heading" className="text-xl font-bold">
        Send receipts from Telegram
      </h2>
      {code ? (
        <>
          <p>
            Your code is{" "}
            <strong className="font-mono text-2xl tracking-widest">
              {code.code}
            </strong>
            . It works for 10 minutes.
          </p>
          {code.bot_link && (
            <a
              href={code.bot_link}
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ size: "lg" })}
            >
              <Send aria-hidden="true" />
              Open Telegram
            </a>
          )}
          <p className="text-sm text-muted-foreground">
            Or send the code to the bot yourself.
          </p>
        </>
      ) : (
        <Button variant="secondary" size="lg" onClick={getCode}>
          <Send aria-hidden="true" />
          Link Telegram
        </Button>
      )}
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </section>
  );
}

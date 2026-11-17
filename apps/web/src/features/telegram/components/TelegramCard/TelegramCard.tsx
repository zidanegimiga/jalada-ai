"use client";

import { Send } from "lucide-react";
import { useState } from "react";

import { Button, buttonVariants } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";

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
      className="flex flex-col gap-3 rounded-card border border-border bg-card p-card"
    >
      <h2 id="telegram-heading" className="text-title">
        Send receipts from Telegram
      </h2>
      {code ? (
        <>
          <p>
            Your code is{" "}
            <strong className="font-mono text-amount tracking-widest">
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
          <p className="text-small text-muted-foreground">
            Or send the code to the bot yourself.
          </p>
        </>
      ) : (
        <Button variant="secondary" size="lg" onClick={getCode}>
          <Send aria-hidden="true" />
          Link Telegram
        </Button>
      )}
      <FormError message={error} />
    </section>
  );
}

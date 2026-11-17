"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { Dialog } from "@/shared/components/Dialog";
import { FormError } from "@/shared/components/FormError";
import { Skeleton } from "@/shared/components/Skeleton";

type Loaded =
  { state: "loading" } | { state: "ready"; text: string } | { state: "failed" };

/** How long "Copied" stays before the button reads Copy again. */
const COPIED_MS = 2000;

/** Opens a pasted or forwarded message in place, with a button to copy its text. */
export function MessageDialog({
  evidenceId,
  received,
}: {
  evidenceId: string;
  received: string;
}) {
  const [message, setMessage] = useState<Loaded>({ state: "loading" });
  const [copied, setCopied] = useState(false);

  async function load(open: boolean) {
    if (!open || message.state === "ready") return;
    setMessage({ state: "loading" });
    const response = await fetch(`/v1/evidence/${evidenceId}/file`);
    setMessage(
      response.ok
        ? { state: "ready", text: await response.text() }
        : { state: "failed" },
    );
  }

  async function copy() {
    if (message.state !== "ready") return;
    await navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), COPIED_MS);
  }

  return (
    <Dialog
      title="Message"
      description={received}
      onOpenChange={load}
      trigger={
        <button
          type="button"
          className="inline-flex min-h-tap min-w-tap items-center justify-end underline underline-offset-4"
        >
          <span aria-hidden="true">Open</span>
          <span className="sr-only">Open message</span>
        </button>
      }
    >
      {message.state === "loading" && (
        <div
          aria-busy="true"
          className="flex flex-col gap-2 rounded-inset bg-muted p-4"
        >
          <Skeleton className="h-4 w-full bg-border" />
          <Skeleton className="h-4 w-11/12 bg-border" />
          <Skeleton className="h-4 w-2/3 bg-border" />
        </div>
      )}
      {message.state === "ready" && (
        <p className="overflow-y-auto rounded-inset bg-muted p-4 whitespace-pre-wrap break-words">
          {message.text}
        </p>
      )}
      <FormError
        message={
          message.state === "failed"
            ? "Could not open the message. Try again."
            : null
        }
      />
      <Button
        size="lg"
        onClick={copy}
        disabled={message.state !== "ready"}
        className="w-full"
      >
        {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
        <span aria-live="polite">{copied ? "Copied" : "Copy text"}</span>
      </Button>
    </Dialog>
  );
}

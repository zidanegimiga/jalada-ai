"use client";

import { Check, Copy, ExternalLink } from "lucide-react";
import { useEffect, useState, type ReactElement } from "react";

import { Button } from "@/shared/components/Button";
import { Dialog } from "@/shared/components/Dialog";
import { FormError } from "@/shared/components/FormError";
import { Skeleton } from "@/shared/components/Skeleton";

type Loaded =
  { state: "loading" } | { state: "ready"; text: string } | { state: "failed" };

/** How long "Copied" stays before the button reads Copy text again. */
const COPIED_MS = 2000;

type Kind = "message" | "photo" | "pdf";

function kindOf(contentType: string): Kind {
  if (contentType.startsWith("text/")) return "message";
  return contentType === "application/pdf" ? "pdf" : "photo";
}

const TITLES: Record<Kind, string> = {
  message: "Message",
  photo: "Photo",
  pdf: "PDF",
};

type EvidenceDialogProps = {
  evidenceId: string;
  contentType: string;
  /** Under the title, such as "Received 17 Nov 2026, 12:15". */
  description?: string;
  /** The control that opens it. */
  trigger: ReactElement;
};

/**
 * Opens what was sent, in place: a message as text with a button to copy it, a photo or a
 * PDF in the sheet with a link to open it full size.
 */
export function EvidenceDialog({
  evidenceId,
  contentType,
  description,
  trigger,
}: EvidenceDialogProps) {
  const kind = kindOf(contentType);
  const file = `/v1/evidence/${evidenceId}/file`;
  return (
    <Dialog title={TITLES[kind]} description={description} trigger={trigger}>
      {kind === "message" ? (
        <MessageBody file={file} />
      ) : (
        <FileBody file={file} kind={kind} />
      )}
    </Dialog>
  );
}

function FileBody({ file, kind }: { file: string; kind: "photo" | "pdf" }) {
  return (
    <>
      {kind === "photo" ? (
        // eslint-disable-next-line @next/next/no-img-element -- the user's own photo, from the API
        <img
          src={file}
          alt="The photo you sent"
          className="max-h-[60dvh] w-full rounded-inset bg-muted object-contain"
        />
      ) : (
        <iframe
          src={file}
          title="The PDF you sent"
          className="h-[60dvh] w-full rounded-inset border border-border bg-muted"
        />
      )}
      <a
        href={file}
        target="_blank"
        rel="noreferrer"
        className="inline-flex min-h-tap items-center justify-center gap-2 rounded-full border border-border font-medium transition-colors hover:bg-muted"
      >
        <ExternalLink aria-hidden="true" className="size-icon" />
        Open full size
      </a>
    </>
  );
}

function MessageBody({ file }: { file: string }) {
  const [message, setMessage] = useState<Loaded>({ state: "loading" });
  const [copied, setCopied] = useState(false);

  // The sheet's content only exists while it is open, so this runs once per opening.
  useEffect(() => {
    let current = true;
    void fetch(file).then(async (response) => {
      const loaded: Loaded = response.ok
        ? { state: "ready", text: await response.text() }
        : { state: "failed" };
      if (current) setMessage(loaded);
    });
    return () => {
      current = false;
    };
  }, [file]);

  async function copy() {
    if (message.state !== "ready") return;
    await navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), COPIED_MS);
  }

  return (
    <>
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
        <p className="overflow-y-auto rounded-inset bg-muted p-4 break-words whitespace-pre-wrap">
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
    </>
  );
}

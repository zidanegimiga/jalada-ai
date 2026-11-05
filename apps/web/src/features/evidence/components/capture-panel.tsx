"use client";

import { Camera, MessageSquareText } from "lucide-react";
import { useRef, useState } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import { pasteText, uploadFile } from "../api";
import { useCapture } from "./use-capture";

const ACCEPTED = "image/jpeg,image/png,image/webp,application/pdf";

export function CapturePanel() {
  const { busy, notice, run } = useCapture();
  const [pasting, setPasting] = useState(false);
  const [text, setText] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  async function onFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) await run(() => uploadFile(file));
    if (fileInput.current) fileInput.current.value = "";
  }

  async function onPaste(event: React.FormEvent) {
    event.preventDefault();
    if (await run(() => pasteText(text))) {
      setText("");
      setPasting(false);
    }
  }

  return (
    <section
      aria-labelledby="capture-heading"
      className="flex flex-col gap-3 rounded-3xl bg-foreground p-5 text-background dark:border dark:border-border dark:bg-card dark:text-card-foreground"
    >
      <h2 id="capture-heading" className="text-xl font-bold">
        Add evidence
      </h2>
      <label className={buttonVariants({ size: "lg" })}>
        <Camera aria-hidden="true" />
        Photo or PDF
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPTED}
          className="sr-only"
          onChange={onFile}
          disabled={busy}
        />
      </label>
      {pasting ? (
        <form onSubmit={onPaste} className="flex flex-col gap-3">
          <Textarea
            aria-label="M-Pesa message"
            placeholder="Paste the M-Pesa message here"
            value={text}
            onChange={(event) => setText(event.target.value)}
            maxLength={5000}
            className="text-foreground"
            required
          />
          <Button type="submit" variant="secondary" size="lg" disabled={busy}>
            Save message
          </Button>
        </form>
      ) : (
        <Button
          variant="secondary"
          size="lg"
          onClick={() => setPasting(true)}
          disabled={busy}
        >
          <MessageSquareText aria-hidden="true" />
          Paste M-Pesa message
        </Button>
      )}
      <p
        role="status"
        className={
          notice?.tone === "error"
            ? "font-medium text-[#ff9a8a]"
            : "font-medium"
        }
      >
        {busy ? "Saving..." : notice?.text}
      </p>
    </section>
  );
}

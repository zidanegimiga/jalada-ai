"use client";

import { ArrowUp } from "lucide-react";
import { useState, type KeyboardEvent } from "react";

import { Button } from "@/shared/components/Button";
import { cn } from "@/shared/styles/cn";

// The API takes questions up to this long.
const MAX_LENGTH = 2000;

type ComposerProps = {
  /** Resolves false when the question was not sent, so it stays in the box. */
  onSend: (question: string) => Promise<boolean>;
  busy: boolean;
};

/** Where the question is typed. Enter sends; Shift and Enter starts a new line. */
export function Composer({ onSend, busy }: ComposerProps) {
  const [question, setQuestion] = useState("");
  const empty = question.trim() === "";

  async function submit() {
    if (empty || busy) return;
    const asked = question;
    setQuestion("");
    if (!(await onSend(asked))) setQuestion(asked);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
      className="flex items-end gap-2 rounded-card border border-border bg-card p-2 shadow-float focus-within:border-ring"
    >
      <label htmlFor="question" className="sr-only">
        Your question
      </label>
      <textarea
        id="question"
        rows={1}
        maxLength={MAX_LENGTH}
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Ask about your money"
        className="field-sizing-content max-h-40 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-body outline-none placeholder:text-muted-foreground"
      />
      <Button
        type="submit"
        size="icon"
        aria-label="Send"
        disabled={empty || busy}
        className={cn("shrink-0", busy && "opacity-60")}
      >
        <ArrowUp aria-hidden="true" className="size-icon" />
      </Button>
    </form>
  );
}

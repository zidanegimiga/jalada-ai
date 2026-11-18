"use client";

import { useEffect, useRef } from "react";

import { FormError } from "@/shared/components/FormError";

import { useAgentChat } from "../../hooks/useAgentChat";
import type { Thread } from "../../types";
import { Composer } from "../Composer";
import { MessageBubble } from "../MessageBubble";
import { Suggestions } from "../Suggestions";
import { ToolActivity } from "../ToolActivity";

/**
 * A conversation with the assistant: the messages, what it is doing now, and the box to
 * ask in, which stays just above the bottom bar on phones.
 */
export function ChatPanel({ initial }: { initial: Thread | null }) {
  const { messages, progress, lookups, error, send } = useAgentChat(initial);
  const end = useRef<HTMLDivElement>(null);
  const busy = progress !== null;

  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end", behavior: "smooth" });
  }, [messages.length, progress]);

  return (
    <div className="flex flex-1 flex-col gap-4">
      {messages.length === 0 ? (
        // Nothing asked yet: the suggestions sit in the middle of the space.
        <div className="flex flex-1 flex-col justify-center">
          <Suggestions
            onPick={(question) => void send(question)}
            disabled={busy}
          />
        </div>
      ) : (
        // Messages gather at the bottom, above the input, as in any chat.
        <ol aria-label="Conversation" className="mt-auto flex flex-col gap-3">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
        </ol>
      )}
      <ToolActivity progress={progress} lookups={lookups} />
      <FormError message={error} />
      <div ref={end} />
      {/* Pinned above the bottom bar on a phone and to the window's foot on a wide screen.
          The fade above it lets messages scroll up behind it, and the strip below it covers
          the gap down to the bar, which hides its own fade on this page. */}
      <div
        data-pinned-composer=""
        className="sticky bottom-[calc(env(safe-area-inset-bottom)+5.75rem)] z-10 pt-2 before:pointer-events-none before:absolute before:inset-x-0 before:-top-8 before:-z-10 before:h-10 before:bg-linear-to-t before:from-background before:to-transparent after:pointer-events-none after:absolute after:inset-x-0 after:top-full after:-z-10 after:h-[calc(env(safe-area-inset-bottom)+6rem)] after:bg-background motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-4 motion-safe:duration-500 lg:bottom-6 lg:after:h-6"
      >
        <Composer onSend={send} busy={busy} />
      </div>
    </div>
  );
}

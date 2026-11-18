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
        <Suggestions
          onPick={(question) => void send(question)}
          disabled={busy}
        />
      ) : (
        <ol aria-label="Conversation" className="flex flex-col gap-3">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
        </ol>
      )}
      <ToolActivity progress={progress} lookups={lookups} />
      <FormError message={error} />
      <div ref={end} />
      <div className="sticky bottom-[calc(env(safe-area-inset-bottom)+6rem)] mt-auto lg:bottom-6">
        <Composer onSend={send} busy={busy} />
      </div>
    </div>
  );
}

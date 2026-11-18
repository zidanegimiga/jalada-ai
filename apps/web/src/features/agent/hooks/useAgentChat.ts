"use client";

import { useState } from "react";

import { ask } from "../api/agent.api";
import { useThreadAnswered } from "./useThreadList";
import type { ChatMessage, Progress, Thread } from "../types";

const STARTING: Progress = { stage: "thinking", tool: null, label: null };

/**
 * One conversation in the browser: the messages so far, what the assistant is doing, and
 * sending the next question. A new conversation gets its id from the first answer.
 */
export function useAgentChat(initial: Thread | null) {
  const answered = useThreadAnswered();
  const [threadId, setThreadId] = useState(initial?.id ?? null);
  // A new conversation is named after its first question, as the API names it.
  const [title, setTitle] = useState(initial?.title ?? null);
  const [messages, setMessages] = useState<ChatMessage[]>(
    initial?.messages ?? [],
  );
  const [progress, setProgress] = useState<Progress | null>(null);
  // Lookups made so far in this turn. Most take milliseconds, so they are kept on show
  // until the answer comes rather than flashing past.
  const [lookups, setLookups] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  /** False when the question was not sent, so the composer can keep it. */
  async function send(question: string): Promise<boolean> {
    const text = question.trim();
    if (!text || progress) return false;
    setError(null);
    setLookups([]);
    setProgress(STARTING);
    const asked: ChatMessage = {
      role: "person",
      text,
      at: new Date().toISOString(),
    };
    setMessages((previous) => [...previous, asked]);
    try {
      await ask(text, threadId, (event) => {
        if (event.event === "progress") {
          const { label } = event.data;
          if (event.data.stage === "looking_up" && label)
            setLookups((previous) => [...previous, label]);
          setProgress(event.data);
        } else if (event.event === "answer") {
          setThreadId(event.data.thread_id);
          const named = title ?? text;
          setTitle(named);
          answered({
            id: event.data.thread_id,
            title: named,
            updated_at: new Date().toISOString(),
          });
          setMessages((previous) => [
            ...previous,
            {
              role: "assistant",
              text: event.data.text,
              at: new Date().toISOString(),
              actions: event.data.actions ?? [],
            },
          ]);
          // The address follows the conversation, so a reload opens it again.
          window.history.replaceState(
            null,
            "",
            `/ask?thread=${event.data.thread_id}`,
          );
        } else {
          setError(event.data.message);
        }
      });
      return true;
    } catch (problem) {
      // Nothing was asked: take the question back off the list for the person to resend.
      setMessages((previous) => previous.filter((m) => m !== asked));
      setError(
        problem instanceof Error
          ? problem.message
          : "The assistant did not answer.",
      );
      return false;
    } finally {
      setProgress(null);
      setLookups([]);
    }
  }

  return { threadId, messages, progress, lookups, error, send };
}

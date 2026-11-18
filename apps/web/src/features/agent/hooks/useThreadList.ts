"use client";

import { createContext, useContext, useState } from "react";

import type { ThreadSummary } from "../types";

/** Tells the history that a conversation was just answered, so it moves to the top. */
export const ThreadAnswered = createContext<(thread: ThreadSummary) => void>(
  () => {},
);

export function useThreadAnswered() {
  return useContext(ThreadAnswered);
}

/**
 * The conversations in the history, kept up to date as answers arrive, so a new conversation
 * shows at once without fetching the page again. A change of page starts from the server's
 * list again.
 */
export function useThreadList(
  threads: ThreadSummary[],
  current: string | null,
) {
  const [fromServer, setFromServer] = useState({ threads, current });
  const [list, setList] = useState(threads);
  const [selected, setSelected] = useState(current);
  if (fromServer.threads !== threads || fromServer.current !== current) {
    setFromServer({ threads, current });
    setList(threads);
    setSelected(current);
  }

  function answered(thread: ThreadSummary) {
    setList((previous) => [
      thread,
      ...previous.filter((item) => item.id !== thread.id),
    ]);
    setSelected(thread.id);
  }

  return { threads: list, current: selected, answered };
}

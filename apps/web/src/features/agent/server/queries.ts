import "server-only";

import { apiGet } from "@/shared/api/server-api";

import type { Thread, ThreadSummary } from "../types";

/** The person's conversations, latest first. Null when the assistant is not available. */
export async function getThreads(): Promise<ThreadSummary[] | null> {
  return apiGet<ThreadSummary[]>("/v1/assistant/threads");
}

/** One conversation with its messages, or null if it is not the person's. */
export async function getThread(id: string): Promise<Thread | null> {
  return apiGet<Thread>(`/v1/assistant/threads/${encodeURIComponent(id)}`);
}

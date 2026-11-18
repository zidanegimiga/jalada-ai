import type { Schema } from "@/shared/api/api-schema";

export type ThreadSummary = Schema<"ThreadSummary">;

export type Thread = Schema<"ThreadResponse">;

export type ChatMessage = Schema<"MessageResponse">;

/** A change the assistant suggested. Nothing changes until the person taps Confirm. */
export type SuggestedAction = Schema<"ActionResponse">;

/** What the assistant is doing while it works, shown above the composer. */
export type Progress = {
  stage: "thinking" | "looking_up" | "checking";
  tool: string | null;
  label: string | null;
};

export type Outcome =
  "answered" | "refused" | "withheld" | "out_of_budget" | "failed";

export type Answer = {
  thread_id: string;
  text: string;
  outcome: Outcome;
  actions?: SuggestedAction[];
};

/** One server-sent event from POST /v1/assistant/messages. */
export type AgentEvent =
  | { event: "progress"; data: Progress }
  | { event: "answer"; data: Answer }
  | { event: "error"; data: { code: string; message: string } };

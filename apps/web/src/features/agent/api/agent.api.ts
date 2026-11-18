import type { AgentEvent, SuggestedAction } from "../types";

/**
 * Splits server-sent events out of the text read so far. Returns the complete events and
 * what is left over, which is the start of an event still arriving.
 */
export function readEvents(buffer: string): {
  events: AgentEvent[];
  rest: string;
} {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: AgentEvent[] = [];
  for (const block of blocks) {
    let name = "";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event: ")) name = line.slice(7);
      else if (line.startsWith("data: ")) data += line.slice(6);
    }
    if (!name || !data) continue;
    try {
      events.push({ event: name, data: JSON.parse(data) } as AgentEvent);
    } catch {
      // A broken event is skipped; the answer or an error still ends the stream.
    }
  }
  return { events, rest };
}

/**
 * Asks the assistant and calls `onEvent` for each event as it arrives. Problems before the
 * stream starts, such as too many questions, are thrown with the API's message.
 */
export async function ask(
  question: string,
  threadId: string | null,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/v1/assistant/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, thread_id: threadId }),
    signal,
  });
  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      data.error?.message ?? "The assistant did not answer. Try again.",
    );
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    const read = readEvents(buffer + value);
    buffer = read.rest;
    read.events.forEach(onEvent);
  }
  readEvents(buffer + "\n\n").events.forEach(onEvent);
}

/** The person's answer to a suggested change. Confirming makes it; the result comes back. */
export async function decide(
  actionId: string,
  decision: "confirm" | "decline",
): Promise<SuggestedAction> {
  const response = await fetch(
    `/v1/assistant/actions/${encodeURIComponent(actionId)}/${decision}`,
    { method: "POST" },
  );
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error?.message ?? "That did not save. Try again.");
  return data as SuggestedAction;
}

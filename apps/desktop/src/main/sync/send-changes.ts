import type { QueuedChange } from "../store/changes";
import type { OpenStore } from "../store/local-store";
import { CHANGE_KINDS } from "./change-kinds";

/** How sending ended: everything went, or it stopped and the rest waits for the next try. */
export type SendResult =
  | { outcome: "sent"; confirmed: number }
  | { outcome: "signed-out"; confirmed: number }
  | { outcome: "later"; confirmed: number };

type Send = {
  apiOrigin: string;
  token: string;
  store: OpenStore;
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  now: () => Date;
  /** A change moved to another state. */
  changed: () => void;
};

type Verdict = "confirmed" | "refused" | "later" | "signed-out";

/** Answers that pass by themselves: the change is sent again later with the same key. */
const PASSING = new Set(["still_running", "too_many_attempts"]);

/**
 * Sends the changes made on this computer, oldest first, one at a time (decision 0029).
 * Each carries its id as the Idempotency-Key, so one sent again after a lost answer is
 * applied once. A refused change waits for the person and the rest carry on; anything that
 * passes by itself, like no connection, stops here and keeps the order.
 */
export async function sendChanges(send: Send): Promise<SendResult> {
  let confirmed = 0;
  for (
    let change = send.store.changes.next();
    change;
    change = send.store.changes.next()
  ) {
    send.store.changes.sending(change.id);
    send.changed();
    const { verdict, problem } = await sendOne(send, change);
    const at = send.now().toISOString();
    if (verdict === "confirmed") {
      send.store.changes.confirmed(change.id, at);
      confirmed += 1;
    } else if (verdict === "refused") {
      send.store.changes.needsAttention(change.id, problem, at);
    } else {
      send.store.changes.later(change.id);
    }
    send.changed();
    if (verdict === "later" || verdict === "signed-out") {
      return { outcome: verdict, confirmed };
    }
  }
  return { outcome: "sent", confirmed };
}

async function sendOne(
  { apiOrigin, token, fetch }: Send,
  change: QueuedChange,
): Promise<{ verdict: Verdict; problem: string }> {
  const kind = CHANGE_KINDS[change.kind];
  if (!kind) {
    return {
      verdict: "refused",
      problem: "This version of the app cannot send this change.",
    };
  }
  const request = kind.request(change.payload);
  let response: Response;
  try {
    response = await fetch(new URL(request.path, apiOrigin).href, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "Idempotency-Key": change.id,
      },
      body: JSON.stringify(request.body),
    });
  } catch {
    return { verdict: "later", problem: "" };
  }
  if (response.ok) return { verdict: "confirmed", problem: "" };
  if (response.status === 401) return { verdict: "signed-out", problem: "" };
  if (response.status >= 500) return { verdict: "later", problem: "" };
  const error = await errorOf(response);
  if (PASSING.has(error.code)) return { verdict: "later", problem: "" };
  return { verdict: "refused", problem: error.message };
}

async function errorOf(
  response: Response,
): Promise<{ code: string; message: string }> {
  const fallback = {
    code: "",
    message: "The server did not accept this change.",
  };
  try {
    const body = (await response.json()) as {
      error?: { code?: string; message?: string };
    };
    return {
      code: body.error?.code ?? "",
      message: body.error?.message ?? fallback.message,
    };
  } catch {
    return fallback;
  }
}

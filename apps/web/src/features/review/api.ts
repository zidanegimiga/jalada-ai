import type { Entry, EntryValues } from "./types";

async function send<T = Entry>(
  path: string,
  method: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error?.message ?? "That did not save. Try again.");
  return data as T;
}

export function confirmEntry(entryId: string): Promise<Entry> {
  return send(`/v1/entries/${entryId}/confirm`, "POST");
}

export function correctEntry(
  entryId: string,
  values: EntryValues,
): Promise<Entry> {
  return send(`/v1/entries/${entryId}`, "PATCH", values);
}

export function enterByHand(
  evidenceId: string,
  values: EntryValues,
): Promise<Entry> {
  return send(`/v1/evidence/${evidenceId}/entry`, "POST", values);
}

export async function markNotATransaction(evidenceId: string): Promise<void> {
  await send<unknown>(`/v1/evidence/${evidenceId}/not-a-transaction`, "POST");
}

export function acceptMatch(suggestionId: string): Promise<Entry> {
  return send(`/v1/suggestions/${suggestionId}/accept`, "POST");
}

export async function declineMatch(suggestionId: string): Promise<void> {
  await send<unknown>(`/v1/suggestions/${suggestionId}/decline`, "POST");
}

export function sayHowPaid(
  entryId: string,
  paidWith: "cash" | "card",
): Promise<Entry> {
  return send(`/v1/receipts/${entryId}/paid`, "POST", { paid_with: paidWith });
}

export function undoMatch(suggestionId: string): Promise<Entry> {
  return send(`/v1/suggestions/${suggestionId}/undo`, "POST");
}

/** Confirms the listed payments that are still ready. The rest stay on To check. */
export function confirmAll(
  entryIds: string[],
): Promise<{ confirmed: Entry[] }> {
  return send(`/v1/review/confirm-all`, "POST", { entry_ids: entryIds });
}

/** The paybill account this payment went to is mine, so it is a transfer. */
export function sayOwnAccount(entryId: string): Promise<Entry> {
  return send(`/v1/payments/${entryId}/own-account`, "POST");
}

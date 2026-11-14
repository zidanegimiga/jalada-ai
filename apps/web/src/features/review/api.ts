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

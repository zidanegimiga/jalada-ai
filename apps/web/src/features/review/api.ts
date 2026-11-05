import type { Entry, EntryValues } from "./types";

async function send(
  path: string,
  method: string,
  body?: unknown,
): Promise<Entry> {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error?.message ?? "That did not save. Try again.");
  return data as Entry;
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

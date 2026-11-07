import type { Schema } from "@/lib/api-schema";

export type EvidenceItem = Schema<"EvidenceResponse">;

async function parse(response: Response): Promise<EvidenceItem> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error?.message ?? "That did not save. Try again.");
  return data as EvidenceItem;
}

export async function uploadFile(file: File): Promise<EvidenceItem> {
  const form = new FormData();
  form.append("file", file);
  return parse(await fetch("/v1/evidence", { method: "POST", body: form }));
}

export async function pasteText(text: string): Promise<EvidenceItem> {
  return parse(
    await fetch("/v1/evidence/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }),
  );
}

/** The latest state of one piece of evidence, or null if it could not be read. */
export async function getEvidence(id: string): Promise<EvidenceItem | null> {
  const response = await fetch(`/v1/evidence/${encodeURIComponent(id)}`);
  return response.ok ? ((await response.json()) as EvidenceItem) : null;
}

/** Evidence the worker has not finished with yet. */
export function isStillReading(item: EvidenceItem): boolean {
  return item.status === "received" || item.status === "processing";
}

export type EvidenceItem = {
  id: string;
  source: "web_upload" | "web_paste" | "telegram";
  kind: string;
  status: string;
  content_type: string;
  size_bytes: number;
  received_at: string;
  duplicate: boolean;
};

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

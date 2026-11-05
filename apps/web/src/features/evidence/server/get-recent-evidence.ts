import "server-only";

import { apiGet } from "@/lib/server-api";

import type { EvidenceItem } from "../api";

export async function getRecentEvidence(): Promise<EvidenceItem[]> {
  return (await apiGet<{ items: EvidenceItem[] }>("/v1/evidence"))?.items ?? [];
}

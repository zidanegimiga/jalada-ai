import "server-only";

import { apiGet } from "@/shared/api/server-api";

import type { EvidenceItem } from "../api/evidence.api";

export async function getRecentEvidence(): Promise<EvidenceItem[]> {
  return (await apiGet<{ items: EvidenceItem[] }>("/v1/evidence"))?.items ?? [];
}

import "server-only";

import { apiGet } from "@/lib/server-api";

import type { Certificate } from "../types";

export async function getCertificate(id: string): Promise<Certificate | null> {
  return apiGet<Certificate>(`/v1/certificates/${encodeURIComponent(id)}`);
}

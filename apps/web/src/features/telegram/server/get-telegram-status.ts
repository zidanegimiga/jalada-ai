import "server-only";

import type { Schema } from "@/lib/api-schema";
import { apiGet } from "@/lib/server-api";

export type TelegramStatus = Schema<"TelegramStatus">;

export async function getTelegramStatus(): Promise<TelegramStatus> {
  return (
    (await apiGet<TelegramStatus>("/v1/telegram/status")) ?? {
      available: false,
      linked: false,
    }
  );
}

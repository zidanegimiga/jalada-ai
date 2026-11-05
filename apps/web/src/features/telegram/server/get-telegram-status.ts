import "server-only";

import { apiGet } from "@/lib/server-api";

export type TelegramStatus = { available: boolean; linked: boolean };

export async function getTelegramStatus(): Promise<TelegramStatus> {
  return (
    (await apiGet<TelegramStatus>("/v1/telegram/status")) ?? {
      available: false,
      linked: false,
    }
  );
}

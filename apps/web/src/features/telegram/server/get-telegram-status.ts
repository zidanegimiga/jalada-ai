import "server-only";

import { cache } from "react";

import type { Schema } from "@/lib/api-schema";
import { apiGet } from "@/lib/server-api";

export type TelegramStatus = Schema<"TelegramStatus">;

/** One request per page, however many parts of the page ask. */
export const getTelegramStatus = cache(async (): Promise<TelegramStatus> => {
  return (
    (await apiGet<TelegramStatus>("/v1/telegram/status")) ?? {
      available: false,
      linked: false,
    }
  );
});

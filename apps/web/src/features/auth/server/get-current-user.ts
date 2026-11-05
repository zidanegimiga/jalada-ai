import "server-only";

import { apiGet } from "@/lib/server-api";

import type { User } from "../api";

/** Asks the API who owns the session cookie. Null when signed out or the session expired. */
export function getCurrentUser(): Promise<User | null> {
  return apiGet<User>("/v1/me");
}

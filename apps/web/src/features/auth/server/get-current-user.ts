import "server-only";

import { cache } from "react";

import { apiGet } from "@/shared/api/server-api";

import type { User } from "../api/auth.api";

/**
 * Asks the API who owns the session cookie. Null when signed out or the session expired.
 * Asked once per page, however many parts of the page need it.
 */
export const getCurrentUser = cache((): Promise<User | null> => {
  return apiGet<User>("/v1/me");
});

import "server-only";

import { cookies } from "next/headers";

import type { User } from "../api";
import { SESSION_COOKIE } from "../session";

/** Asks the API who owns the session cookie. Null when signed out or the session expired. */
export async function getCurrentUser(): Promise<User | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  const response = await fetch(`${process.env.API_URL ?? "http://localhost:8000"}/v1/me`, {
    headers: { Cookie: `${SESSION_COOKIE}=${token}` },
  });
  return response.ok ? ((await response.json()) as User) : null;
}

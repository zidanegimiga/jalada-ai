import "server-only";

import { cookies } from "next/headers";

import { SESSION_COOKIE } from "./session-cookie";

/** GET from the API on the server, passing the user's session along. Null on any failure. */
export async function apiGet<T>(path: string): Promise<T | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  const response = await fetch(
    `${process.env.API_URL ?? "http://localhost:8000"}${path}`,
    {
      headers: { Cookie: `${SESSION_COOKIE}=${token}` },
    },
  );
  return response.ok ? ((await response.json()) as T) : null;
}

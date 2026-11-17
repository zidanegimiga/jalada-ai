import "server-only";

/** GET from the API on the server, for public answers that need no session. */
export async function publicApiGet<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(
      `${process.env.API_URL ?? "http://localhost:8000"}${path}`,
    );
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null;
  }
}

import type { ServerEntry } from "../store/entries";
import type { OpenStore } from "../store/local-store";

/** How a pull ended. Only "pulled" changes what is on this computer. */
export type PullResult =
  | { outcome: "pulled"; entries: number; at: string }
  | { outcome: "signed-out" }
  | { outcome: "unreachable" };

export const LAST_PULLED = "ledger_pulled_at";

/** Enough for a few years of records; a runaway server answer cannot loop forever. */
const MAX_PAGES = 200;

type Pull = {
  apiOrigin: string;
  token: string;
  store: OpenStore;
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  now: () => Date;
};

/**
 * Copies the person's confirmed entries from the server to this computer, page by page,
 * newest first (decision 0029). Each page is saved as it arrives, so a dropped connection
 * keeps what came before. Entries removed on the server stay here until the change feed
 * (DSK-06) says so.
 */
export async function pullLedger({
  apiOrigin,
  token,
  store,
  fetch,
  now,
}: Pull): Promise<PullResult> {
  const at = now().toISOString();
  let cursor: string | null = null;
  let saved = 0;
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const url = new URL("/v1/entries", apiOrigin);
    if (cursor) url.searchParams.set("cursor", cursor);
    let response: Response;
    try {
      response = await fetch(url.href, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      return { outcome: "unreachable" };
    }
    if (response.status === 401) return { outcome: "signed-out" };
    if (!response.ok) return { outcome: "unreachable" };
    const body = (await response.json()) as {
      items: ServerEntry[];
      next_cursor: string | null;
    };
    store.entries.saveFromServer(body.items, at);
    saved += body.items.length;
    cursor = body.next_cursor;
    if (!cursor) break;
  }
  store.syncState.set(LAST_PULLED, at);
  return { outcome: "pulled", entries: saved, at };
}

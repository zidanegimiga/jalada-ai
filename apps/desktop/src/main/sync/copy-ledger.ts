import type { ServerEntry } from "../store/entries";

import { LAST_PULLED, type Pull, type PullResult } from "./pull-types";

/** Enough for a few years of records; a runaway server answer cannot loop forever. */
const MAX_PAGES = 200;

/**
 * Copies the person's confirmed entries from the server to this computer, page by page,
 * newest first. Each page is saved as it arrives, so a dropped connection keeps what came
 * before. For a server without the change feed: entries that leave the ledger there stay
 * here.
 */
export async function copyWholeLedger({
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

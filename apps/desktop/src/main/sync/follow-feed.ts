import type { ServerEntry } from "../store/entries";
import { LAST_PULLED, type Pull, type PullResult } from "./pull-types";

/** Where the change feed got to on this computer. */
export const FEED_POSITION = "entries_feed_after";

/** Enough to catch up after a long time away; a runaway answer cannot loop forever. */
const MAX_PAGES = 500;

type FeedPage = {
  changes: { id: string; version: number; entry: ServerEntry | null }[];
  next: string;
  more: boolean;
};

/** The feed's answer, or why there is none. "missing" is a server without the feed. */
export type FeedRead = PullResult | { outcome: "missing" };

/**
 * Brings the ledger here up to date from the server's change feed (decision 0029): only
 * what was saved since last time, oldest first. Confirmed entries are kept; any other state
 * means the entry left the ledger, so the copy here goes too. Each page and the position
 * after it are saved together, so a dropped connection resumes where it stopped.
 */
export async function followFeed({
  apiOrigin,
  token,
  store,
  fetch,
  now,
}: Pull): Promise<FeedRead> {
  const at = now().toISOString();
  let changed = 0;
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const url = new URL("/v1/sync/entries", apiOrigin);
    const after = store.syncState.get(FEED_POSITION);
    if (after) url.searchParams.set("after", after);
    let response: Response;
    try {
      response = await fetch(url.href, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      return { outcome: "unreachable" };
    }
    if (response.status === 401) return { outcome: "signed-out" };
    if (response.status === 404) return { outcome: "missing" };
    if (!response.ok) return { outcome: "unreachable" };
    const body = (await response.json()) as FeedPage;
    const kept = body.changes.flatMap((c) =>
      c.entry?.status === "confirmed"
        ? [{ ...c.entry, version: c.version }]
        : [],
    );
    const gone = body.changes.flatMap((c) =>
      c.entry?.status === "confirmed" ? [] : [c.id],
    );
    store.entries.applyChanges(kept, gone, at, {
      name: FEED_POSITION,
      value: body.next,
    });
    changed += body.changes.length;
    if (!body.more) break;
  }
  store.syncState.set(LAST_PULLED, at);
  return { outcome: "pulled", entries: changed, at };
}

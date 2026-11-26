import { randomUUID } from "node:crypto";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import type { ServerEntry } from "../src/main/store/entries";
import type { KeyProtector } from "../src/main/store/key";
import { LocalStore, type OpenStore } from "../src/main/store/local-store";
import { FEED_POSITION, followFeed } from "../src/main/sync/follow-feed";
import { LAST_PULLED, pullLedger } from "../src/main/sync/pull-ledger";

const keychain: KeyProtector = {
  isSecure: () => true,
  seal: (secret) => Buffer.from([...secret].reverse().join("")),
  open: (sealed) => [...sealed.toString()].reverse().join(""),
};
const API = "https://api.jalada.example";
const NOW = new Date("2026-11-20T09:00:00Z");
type Fetch = (url: string, init: RequestInit) => Promise<Response>;

// Invented entries.
function entry(n: number, status = "confirmed"): ServerEntry {
  return {
    id: `entry-${n}`,
    kind: "transaction",
    status,
    occurred_on: `2026-11-${String(10 + n).padStart(2, "0")}`,
    direction: "out",
    amount_cents: n * 100_00,
    counterparty: `Shop ${n}`,
    category: "groceries",
    category_name: "Food and groceries",
    purpose: "personal",
    mpesa_code: null,
  };
}

const change = (e: ServerEntry, version = 1) => ({
  id: e.id,
  version,
  entry: e,
});
const feed = (changes: unknown[], next: string, more = false) =>
  new Response(JSON.stringify({ changes, next, more }));

const folders: string[] = [];
const opened: OpenStore[] = [];
afterEach(() => {
  for (const store of opened.splice(0)) store.close();
  for (const made of folders.splice(0))
    rmSync(made, { recursive: true, force: true });
});

function openStore(): OpenStore {
  const folder = mkdtempSync(join(tmpdir(), "jalada-feed-"));
  folders.push(folder);
  const store = new LocalStore(folder, keychain).open(randomUUID());
  opened.push(store);
  return store;
}

const read = (store: OpenStore, fetch: Fetch) =>
  followFeed({ apiOrigin: API, token: "t0ken", store, fetch, now: () => NOW });

const shown = (store: OpenStore) =>
  store.entries.list().map((e) => e.counterparty);

describe("following the change feed", () => {
  it("starts from the beginning, keeps confirmed entries and where it got to", async () => {
    const store = openStore();
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValue(
        feed([change(entry(1)), change(entry(2, "needs_review"))], "p1"),
      );

    const result = await read(store, fetch);

    expect(fetch.mock.calls[0]![0]).toBe(`${API}/v1/sync/entries`);
    expect(fetch.mock.calls[0]![1].headers).toEqual({
      Authorization: "Bearer t0ken",
    });
    expect(result).toEqual({
      outcome: "pulled",
      entries: 2,
      at: NOW.toISOString(),
    });
    expect(shown(store)).toEqual(["Shop 1"]);
    expect(store.syncState.get(FEED_POSITION)).toBe("p1");
    expect(store.syncState.get(LAST_PULLED)).toBe(NOW.toISOString());
  });

  it("asks only for what changed since, and drops entries that left the ledger", async () => {
    const store = openStore();
    await read(
      store,
      vi
        .fn<Fetch>()
        .mockResolvedValue(feed([change(entry(1)), change(entry(2))], "p1")),
    );
    const renamed = { ...entry(2), counterparty: "Renamed shop" };
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValue(
        feed([change(entry(1, "rejected"), 2), change(renamed, 3)], "p2"),
      );

    await read(store, fetch);

    expect(fetch.mock.calls[0]![0]).toBe(`${API}/v1/sync/entries?after=p1`);
    expect(shown(store)).toEqual(["Renamed shop"]);
  });

  it("reads page after page while the server has more", async () => {
    const store = openStore();
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValueOnce(feed([change(entry(1))], "p1", true))
      .mockResolvedValueOnce(feed([change(entry(2))], "p2"));

    await read(store, fetch);

    expect(fetch.mock.calls[1]![0]).toBe(`${API}/v1/sync/entries?after=p1`);
    expect(shown(store)).toEqual(["Shop 2", "Shop 1"]);
    expect(store.syncState.get(FEED_POSITION)).toBe("p2");
  });

  it("keeps the pages it got when the connection drops, and resumes there", async () => {
    const store = openStore();
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValueOnce(feed([change(entry(1))], "p1", true))
      .mockRejectedValueOnce(new TypeError("offline"));

    const result = await read(store, fetch);

    expect(result).toEqual({ outcome: "unreachable" });
    expect(shown(store)).toEqual(["Shop 1"]);
    expect(store.syncState.get(FEED_POSITION)).toBe("p1");
    // Not finished, so it does not claim to be up to date.
    expect(store.syncState.get(LAST_PULLED)).toBeNull();
  });

  it("says when the server no longer accepts the session", async () => {
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValue(new Response("{}", { status: 401 }));

    expect(await read(openStore(), fetch)).toEqual({ outcome: "signed-out" });
  });

  it("copies the whole ledger from a server without the feed", async () => {
    const store = openStore();
    const fetch = vi
      .fn<Fetch>()
      .mockImplementation(async (url) =>
        new URL(url).pathname === "/v1/sync/entries"
          ? new Response("{}", { status: 404 })
          : new Response(
              JSON.stringify({ items: [entry(1)], next_cursor: null }),
            ),
      );

    const result = await pullLedger({
      apiOrigin: API,
      token: "t",
      store,
      fetch,
      now: () => NOW,
    });

    expect(result.outcome).toBe("pulled");
    expect(shown(store)).toEqual(["Shop 1"]);
  });
});

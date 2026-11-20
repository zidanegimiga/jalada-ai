import { randomUUID } from "node:crypto";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it, vi, type Mock } from "vitest";

import type { ServerEntry } from "../src/main/store/entries";
import type { KeyProtector } from "../src/main/store/key";
import { LocalStore, type OpenStore } from "../src/main/store/local-store";
import { LedgerSync } from "../src/main/sync/ledger-sync";
import { LAST_PULLED, pullLedger } from "../src/main/sync/pull-ledger";

const keychain: KeyProtector = {
  isSecure: () => true,
  seal: (secret) => Buffer.from([...secret].reverse().join("")),
  open: (sealed) => [...sealed.toString()].reverse().join(""),
};
const API = "https://api.jalada.example";
const NOW = new Date("2026-11-20T09:00:00Z");

// Invented entries.
function entry(n: number): ServerEntry {
  return {
    id: `entry-${n}`,
    kind: "transaction",
    status: "confirmed",
    occurred_on: `2026-11-${String(10 + n).padStart(2, "0")}`,
    direction: n % 2 ? "in" : "out",
    amount_cents: n * 100_00,
    counterparty: `Shop ${n}`,
    category: "groceries",
    category_name: "Food and groceries",
    purpose: "personal",
    mpesa_code: null,
  };
}

const page = (items: ServerEntry[], next: string | null) =>
  new Response(JSON.stringify({ items, next_cursor: next }));

const folders: string[] = [];
const opened: OpenStore[] = [];
afterEach(() => {
  for (const store of opened.splice(0)) store.close();
  for (const made of folders.splice(0))
    rmSync(made, { recursive: true, force: true });
});

function localStore(): LocalStore {
  const folder = mkdtempSync(join(tmpdir(), "jalada-sync-"));
  folders.push(folder);
  return new LocalStore(folder, keychain);
}

function openStore(): OpenStore {
  const store = localStore().open(randomUUID());
  opened.push(store);
  return store;
}

describe("pulling the ledger", () => {
  it("copies every page, sending the session as a Bearer token", async () => {
    const store = openStore();
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(page([entry(1), entry(2)], "next"))
      .mockResolvedValueOnce(page([entry(3)], null));

    const result = await pullLedger({
      apiOrigin: API,
      token: "t0ken",
      store,
      fetch,
      now: () => NOW,
    });

    expect(result).toEqual({
      outcome: "pulled",
      entries: 3,
      at: NOW.toISOString(),
    });
    expect(store.entries.count()).toBe(3);
    expect(fetch.mock.calls[1]![0]).toBe(`${API}/v1/entries?cursor=next`);
    expect(fetch.mock.calls[0]![1].headers).toEqual({
      Authorization: "Bearer t0ken",
    });
    expect(store.syncState.get(LAST_PULLED)).toBe(NOW.toISOString());
  });

  it("keeps the pages it got when the connection drops partway", async () => {
    const store = openStore();
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(page([entry(1)], "next"))
      .mockRejectedValueOnce(new TypeError("offline"));

    const result = await pullLedger({
      apiOrigin: API,
      token: "t",
      store,
      fetch,
      now: () => NOW,
    });

    expect(result).toEqual({ outcome: "unreachable" });
    expect(store.entries.count()).toBe(1);
    // Not finished, so it does not claim to be up to date.
    expect(store.syncState.get(LAST_PULLED)).toBeNull();
  });

  it("says when the server no longer accepts the session", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 401 }));

    const result = await pullLedger({
      apiOrigin: API,
      token: "old",
      store: openStore(),
      fetch,
      now: () => NOW,
    });

    expect(result).toEqual({ outcome: "signed-out" });
  });
});

describe("keeping the ledger on this computer", () => {
  type Fetch = (url: string, init: RequestInit) => Promise<Response>;

  function sync(fetch: Mock<Fetch>, store: LocalStore = localStore()) {
    const ports = {
      apiOrigin: API,
      store,
      fetch,
      token: () => "t",
      sessionEnded: vi.fn(),
      changed: vi.fn(),
      failed: vi.fn(),
      now: () => NOW,
    };
    return { ledger: new LedgerSync(ports), ports };
  }
  const account = () => ({
    id: randomUUID(),
    email: "amina@example.com",
    name: "Amina",
  });

  it("copies the ledger after sign-in and reads it back from this computer", async () => {
    const { ledger } = sync(
      vi.fn<Fetch>().mockResolvedValue(page([entry(1), entry(2)], null)),
    );

    ledger.switchTo(account());
    await ledger.pull();

    expect(ledger.list(10, 0).map((e) => e.counterparty)).toEqual([
      "Shop 2",
      "Shop 1",
    ]);
    expect(ledger.status()).toEqual({
      entries: 2,
      updatedAt: NOW.toISOString(),
      updating: false,
    });
    ledger.switchTo(null);
  });

  it("still reads the copy here when the server cannot be reached", async () => {
    const fetch = vi.fn<Fetch>().mockResolvedValueOnce(page([entry(1)], null));
    const { ledger } = sync(fetch);
    ledger.switchTo(account());
    await ledger.pull();
    fetch.mockRejectedValue(new TypeError("offline"));

    await ledger.pull();

    expect(ledger.list(10, 0)).toHaveLength(1);
    ledger.switchTo(null);
  });

  it("runs one pull at a time", async () => {
    const fetch = vi.fn<Fetch>().mockResolvedValue(page([], null));
    const { ledger } = sync(fetch);
    ledger.switchTo(account());

    await Promise.all([ledger.pull(), ledger.pull(), ledger.pull()]);

    // One for sign-in, joined by the three asked for while it ran.
    expect(fetch).toHaveBeenCalledTimes(1);
    ledger.switchTo(null);
  });

  it("asks to sign in again when the server ends the session", async () => {
    const { ledger, ports } = sync(
      vi.fn<Fetch>().mockResolvedValue(new Response("{}", { status: 401 })),
    );

    ledger.switchTo(account());
    await ledger.pull();

    expect(ports.sessionEnded).toHaveBeenCalled();
    ledger.switchTo(null);
  });

  it("shows nothing once signed out", async () => {
    const { ledger } = sync(
      vi.fn<Fetch>().mockResolvedValue(page([entry(1)], null)),
    );
    ledger.switchTo(account());
    await ledger.pull();

    ledger.switchTo(null);

    expect(ledger.list(10, 0)).toEqual([]);
    expect(ledger.status().entries).toBe(0);
  });

  it("says so when records cannot be kept on this computer", () => {
    const folder = mkdtempSync(join(tmpdir(), "jalada-sync-"));
    folders.push(folder);
    const insecure = new LocalStore(folder, {
      ...keychain,
      isSecure: () => false,
    });
    const { ledger, ports } = sync(vi.fn<Fetch>(), insecure);

    ledger.switchTo(account());

    expect(ports.failed).toHaveBeenCalledWith(
      expect.stringMatching(/no secure place/),
    );
    expect(ledger.list(10, 0)).toEqual([]);
  });
});

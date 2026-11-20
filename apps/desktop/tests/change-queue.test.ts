import { randomUUID } from "node:crypto";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it, vi, type Mock } from "vitest";

import type { KeyProtector } from "../src/main/store/key";
import { LocalStore, type OpenStore } from "../src/main/store/local-store";
import { CHANGE_KINDS } from "../src/main/sync/change-kinds";
import { LedgerSync } from "../src/main/sync/ledger-sync";
import { sendChanges } from "../src/main/sync/send-changes";

const keychain: KeyProtector = {
  isSecure: () => true,
  seal: (secret) => Buffer.from([...secret].reverse().join("")),
  open: (sealed) => [...sealed.toString()].reverse().join(""),
};
const API = "https://api.jalada.example";
const NOW = new Date("2026-11-20T09:00:00Z");
type Fetch = (url: string, init: RequestInit) => Promise<Response>;

// Invented messages.
const message = (n: number) =>
  `UK${n}AB12CD Confirmed. Ksh${n},000.00 paid to SAMPLE SHOP on 20/11/26 at 9:00 AM.`;

const folders: string[] = [];
const opened: OpenStore[] = [];
afterEach(() => {
  for (const store of opened.splice(0)) store.close();
  for (const made of folders.splice(0))
    rmSync(made, { recursive: true, force: true });
});

function localStore(): LocalStore {
  const folder = mkdtempSync(join(tmpdir(), "jalada-changes-"));
  folders.push(folder);
  return new LocalStore(folder, keychain);
}

function openStore(store = localStore(), account = randomUUID()): OpenStore {
  const open = store.open(account);
  opened.push(open);
  return open;
}

let ids = 0;
function add(store: OpenStore, text: string): string {
  ids += 1;
  const id = `change-${ids}`;
  store.changes.add({
    id,
    kind: "pasted_message",
    payload: { text },
    summary: text,
    createdAt: NOW.toISOString(),
  });
  return id;
}

const accepted = () => new Response("{}", { status: 201 });
const refused = (status: number, code: string, message: string) =>
  new Response(JSON.stringify({ error: { code, message } }), { status });

function send(store: OpenStore, fetch: Mock<Fetch>) {
  return sendChanges({
    apiOrigin: API,
    token: "t0ken",
    store,
    fetch,
    now: () => NOW,
    changed: vi.fn(),
  });
}

const states = (store: OpenStore) =>
  store.changes.list().map((change) => [change.id, change.state]);

describe("keeping changes on this computer", () => {
  it("keeps them in order until the server has them, even after closing", () => {
    const store = localStore();
    const account = randomUUID();
    const first = openStore(store, account);
    const one = add(first, message(1));
    const two = add(first, message(2));
    first.close();
    opened.pop();

    const again = openStore(store, account);

    expect(again.changes.next()?.id).toBe(one);
    expect(again.changes.unsent()).toBe(2);
    expect(states(again)).toEqual([
      [two, "saved"],
      [one, "saved"],
    ]);
  });

  it("goes again with a change that was cut off while sending", () => {
    const store = openStore();
    const id = add(store, message(1));
    store.changes.sending(id);

    expect(store.changes.next()).toMatchObject({ id, attempts: 1 });
  });
});

describe("changes the person looks at", () => {
  it("sends a refused one again, in its place, without the old reason", () => {
    const store = openStore();
    const one = add(store, message(1));
    add(store, message(2));
    store.changes.sending(one);
    store.changes.needsAttention(one, "Refused.", NOW.toISOString());

    expect(store.changes.tryAgain(one)).toBe(true);

    expect(store.changes.next()?.id).toBe(one);
    expect(store.changes.list()[1]).toMatchObject({
      id: one,
      state: "saved",
      problem: null,
    });
  });

  it("only sends again what needs attention", () => {
    const store = openStore();
    const id = add(store, message(1));

    expect(store.changes.tryAgain(id)).toBe(false);
    expect(store.changes.tryAgain("no-such-change")).toBe(false);
  });

  it("drops one not yet sent, never one on its way or sent", () => {
    const store = openStore();
    const waiting = add(store, message(1));
    const onItsWay = add(store, message(2));
    const sent = add(store, message(3));
    store.changes.sending(onItsWay);
    store.changes.confirmed(sent, NOW.toISOString());

    expect(store.changes.discard(waiting)).toBe(true);
    expect(store.changes.discard(onItsWay)).toBe(false);
    expect(store.changes.discard(sent)).toBe(false);
    expect(store.changes.list().map((c) => c.id)).toEqual([sent, onItsWay]);
  });

  it("forgets sent changes after a while, and nothing else", () => {
    const store = openStore();
    const old = add(store, message(1));
    const waiting = add(store, message(2));
    store.changes.confirmed(old, "2026-11-01T09:00:00.000Z");

    store.changes.clearSentBefore("2026-11-13T09:00:00.000Z");

    expect(store.changes.list().map((c) => c.id)).toEqual([waiting]);
  });
});

describe("sending changes", () => {
  it("sends each in order with its id as the Idempotency-Key", async () => {
    const store = openStore();
    const one = add(store, message(1));
    const two = add(store, message(2));
    const fetch = vi.fn<Fetch>().mockResolvedValue(accepted());

    const result = await send(store, fetch);

    expect(result).toEqual({ outcome: "sent", confirmed: 2 });
    const [url, init] = fetch.mock.calls[0]!;
    expect(url).toBe(`${API}/v1/evidence/text`);
    expect(init).toMatchObject({
      method: "POST",
      headers: {
        Authorization: "Bearer t0ken",
        "Content-Type": "application/json",
        "Idempotency-Key": one,
      },
      body: JSON.stringify({ text: message(1) }),
    });
    expect(fetch.mock.calls[1]![1].headers).toMatchObject({
      "Idempotency-Key": two,
    });
    expect(store.changes.unsent()).toBe(0);
    expect(states(store)).toEqual([
      [two, "confirmed"],
      [one, "confirmed"],
    ]);
  });

  it("stops without a connection and keeps the order for next time", async () => {
    const store = openStore();
    const one = add(store, message(1));
    add(store, message(2));
    const fetch = vi.fn<Fetch>().mockRejectedValue(new TypeError("offline"));

    const result = await send(store, fetch);

    expect(result).toEqual({ outcome: "later", confirmed: 0 });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(store.changes.next()?.id).toBe(one);
    expect(store.changes.unsent()).toBe(2);
  });

  it("tries again later after a server failure or a busy server", async () => {
    for (const answer of [
      new Response("oops", { status: 503 }),
      refused(409, "still_running", "Still saving."),
      refused(429, "too_many_attempts", "Too many."),
    ]) {
      const store = openStore();
      const id = add(store, message(1));

      const result = await send(
        store,
        vi.fn<Fetch>().mockResolvedValue(answer),
      );

      expect(result.outcome).toBe("later");
      expect(states(store)).toEqual([[id, "saved"]]);
    }
  });

  it("sets a refused change aside with the reason and sends the rest", async () => {
    const store = openStore();
    const one = add(store, message(1));
    const two = add(store, message(2));
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValueOnce(refused(422, "empty", "There is nothing to save."))
      .mockResolvedValueOnce(accepted());

    const result = await send(store, fetch);

    expect(result).toEqual({ outcome: "sent", confirmed: 1 });
    expect(store.changes.list()).toMatchObject([
      { id: two, state: "confirmed", problem: null },
      {
        id: one,
        state: "needs_attention",
        problem: "There is nothing to save.",
      },
    ]);
  });

  it("stops when the server no longer accepts the session", async () => {
    const store = openStore();
    add(store, message(1));
    const fetch = vi
      .fn<Fetch>()
      .mockResolvedValue(new Response("{}", { status: 401 }));

    const result = await send(store, fetch);

    expect(result.outcome).toBe("signed-out");
    expect(store.changes.unsent()).toBe(1);
  });
});

describe("pasted messages", () => {
  const kind = CHANGE_KINDS.pasted_message!;

  it("are trimmed, and refused when empty, too long or not text", () => {
    expect(kind.accept("  hello \n")).toEqual({ text: "hello" });
    expect(kind.accept("   ")).toBeNull();
    expect(kind.accept("x".repeat(5001))).toBeNull();
    expect(kind.accept({ text: "hi" })).toBeNull();
  });

  it("are shown as one short line", () => {
    const summary = kind.summary({ text: `${"a ".repeat(60)}\nend` });
    expect(summary).toHaveLength(80);
    expect(summary).not.toContain("\n");
  });
});

describe("changes made in the app", () => {
  function sync(fetch: Mock<Fetch>) {
    const ports = {
      apiOrigin: API,
      store: localStore(),
      fetch,
      token: () => "t",
      sessionEnded: vi.fn(),
      changed: vi.fn(),
      changesChanged: vi.fn(),
      newId: randomUUID,
      failed: vi.fn(),
      now: () => NOW,
    };
    const ledger = new LedgerSync(ports);
    ledger.switchTo({ id: randomUUID(), email: "a@example.com", name: "A" });
    return { ledger, ports };
  }
  const emptyLedger = () =>
    new Response(JSON.stringify({ items: [], next_cursor: null }));

  it("are kept offline and sent before the ledger is refreshed", async () => {
    const fetch = vi.fn<Fetch>().mockRejectedValue(new TypeError("offline"));
    const { ledger } = sync(fetch);
    await ledger.pull();

    expect(ledger.addChange("pasted_message", message(1))).toBe(true);
    await ledger.pull();
    expect(ledger.unsent()).toBe(1);

    fetch.mockReset();
    fetch.mockResolvedValueOnce(accepted()).mockResolvedValue(emptyLedger());
    await ledger.pull();

    expect(fetch.mock.calls.map(([url]) => new URL(url).pathname)).toEqual([
      "/v1/evidence/text",
      "/v1/entries",
    ]);
    expect(ledger.changes()).toMatchObject([{ state: "confirmed" }]);
    ledger.switchTo(null);
  });

  it("sends a change again once the person asks", async () => {
    let answer = () => refused(422, "empty", "Nothing to save.");
    const fetch = vi
      .fn<Fetch>()
      .mockImplementation(async (url) =>
        new URL(url).pathname === "/v1/entries" ? emptyLedger() : answer(),
      );
    const { ledger, ports } = sync(fetch);
    ledger.addChange("pasted_message", message(1));
    await vi.waitFor(() =>
      expect(ledger.changes()).toMatchObject([{ state: "needs_attention" }]),
    );
    await ledger.pull();
    answer = accepted;
    ports.changesChanged.mockClear();

    expect(ledger.tryAgain(ledger.changes()[0]!.id)).toBe(true);

    expect(ports.changesChanged).toHaveBeenCalled();
    await vi.waitFor(() =>
      expect(ledger.changes()).toMatchObject([{ state: "confirmed" }]),
    );
    ledger.switchTo(null);
  });

  it("refuses input that is not a message, and anything when signed out", () => {
    const { ledger } = sync(vi.fn<Fetch>().mockResolvedValue(emptyLedger()));

    expect(ledger.addChange("pasted_message", "")).toBe(false);
    expect(ledger.addChange("delete_everything", message(1))).toBe(false);
    ledger.switchTo(null);
    expect(ledger.addChange("pasted_message", message(1))).toBe(false);
  });

  it("sends a change added while a sync was running", async () => {
    const fetch = vi
      .fn<Fetch>()
      .mockImplementation(async (url) =>
        new URL(url).pathname === "/v1/entries" ? emptyLedger() : accepted(),
      );
    const { ledger } = sync(fetch);
    const running = ledger.pull();

    ledger.addChange("pasted_message", message(1));
    await running;
    await vi.waitFor(() => expect(ledger.unsent()).toBe(0));

    ledger.switchTo(null);
  });
});

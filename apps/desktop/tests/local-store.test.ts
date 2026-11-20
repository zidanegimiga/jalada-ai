import { randomUUID } from "node:crypto";
import {
  existsSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { openDatabase, WrongKey } from "../src/main/store/database";
import type { ServerEntry } from "../src/main/store/entries";
import { NoSecureStore, type KeyProtector } from "../src/main/store/key";
import { LocalStore } from "../src/main/store/local-store";
import { LATEST } from "../src/main/store/migrations";

/** Stands in for the system keychain: seals by reversing, which is enough to tell apart. */
const keychain: KeyProtector = {
  isSecure: () => true,
  seal: (secret) => Buffer.from([...secret].reverse().join("")),
  open: (sealed) => [...sealed.toString()].reverse().join(""),
};

// Invented entries.
function entry(id: string, day: string, counterparty: string): ServerEntry {
  return {
    id,
    kind: "transaction",
    status: "confirmed",
    occurred_on: `2026-11-${day}`,
    direction: "out",
    amount_cents: 245_000,
    counterparty,
    category: "groceries",
    category_name: "Food and groceries",
    purpose: "personal",
    mpesa_code: "SKE3H8Q2LM",
  };
}

const folders: string[] = [];
function folder(): string {
  const made = mkdtempSync(join(tmpdir(), "jalada-store-"));
  folders.push(made);
  return made;
}

afterEach(() => {
  for (const made of folders.splice(0))
    rmSync(made, { recursive: true, force: true });
});

describe("local store", () => {
  it("keeps entries and lists them newest first", () => {
    const store = new LocalStore(folder(), keychain).open(randomUUID());
    store.entries.saveFromServer(
      [entry("a", "10", "Java House"), entry("b", "17", "Naivas Westgate")],
      "2026-11-20T08:00:00Z",
    );

    expect(store.entries.list().map((e) => e.counterparty)).toEqual([
      "Naivas Westgate",
      "Java House",
    ]);
    store.close();
  });

  it("replaces an older copy of the same entry instead of adding another", () => {
    const store = new LocalStore(folder(), keychain).open(randomUUID());
    store.entries.saveFromServer([entry("a", "10", "Java House")], "t1");
    store.entries.saveFromServer(
      [entry("a", "10", "Java House Kimathi")],
      "t2",
    );

    expect(store.entries.count()).toBe(1);
    expect(store.entries.list()[0]?.counterparty).toBe("Java House Kimathi");
    store.close();
  });

  it("leaves nothing readable in the file on disk", () => {
    const place = folder();
    const account = randomUUID();
    const store = new LocalStore(place, keychain).open(account);
    store.entries.saveFromServer([entry("a", "17", "Naivas Westgate")], "t");
    store.close();

    const raw = readFileSync(join(place, "records", `${account}.db`));
    expect(raw.includes(Buffer.from("Naivas"))).toBe(false);
    expect(raw.includes(Buffer.from("SQLite format 3"))).toBe(false);
  });

  it("keeps the key only in sealed form", () => {
    const place = folder();
    const account = randomUUID();
    new LocalStore(place, keychain).open(account).close();

    const sealed = readFileSync(join(place, "keys", `${account}.key`));
    const key = keychain.open(sealed);
    expect(key).toMatch(/^[0-9a-f]{64}$/);
    expect(sealed.includes(Buffer.from(key))).toBe(false);
  });

  it("opens again with the same key, and refuses a wrong one", () => {
    const place = folder();
    const account = randomUUID();
    new LocalStore(place, keychain).open(account).close();
    const reopened = new LocalStore(place, keychain).open(account);
    reopened.close();

    expect(() =>
      openDatabase(join(place, "records", `${account}.db`), "0".repeat(64)),
    ).toThrow(WrongKey);
  });

  it("forgets the database and its key on sign-out", () => {
    const place = folder();
    const account = randomUUID();
    const local = new LocalStore(place, keychain);
    local.open(account).close();

    local.forget(account);

    expect(readdirSync(join(place, "records"))).toEqual([]);
    expect(existsSync(join(place, "keys", `${account}.key`))).toBe(false);
  });

  it("keeps nothing when the computer has no secure place for the key", () => {
    const insecure = { ...keychain, isSecure: () => false };

    expect(() => new LocalStore(folder(), insecure).open(randomUUID())).toThrow(
      NoSecureStore,
    );
  });

  it("refuses an account id that could reach outside its folder", () => {
    const local = new LocalStore(folder(), keychain);

    expect(() => local.open("../../etc/passwd")).toThrow(/account id/);
    expect(() => local.forget("../keys/other")).toThrow(/account id/);
  });

  it("is at the latest table version", () => {
    const place = folder();
    const account = randomUUID();
    new LocalStore(place, keychain).open(account).close();
    const key = keychain.open(
      readFileSync(join(place, "keys", `${account}.key`)),
    );
    const db = openDatabase(join(place, "records", `${account}.db`), key);

    expect(db.pragma("user_version", { simple: true })).toBe(LATEST);
    db.close();
  });
});

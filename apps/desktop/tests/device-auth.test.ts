import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { DeviceAuth, SignInFailed } from "../src/main/auth/device-auth";
import { newSignInRequest, readSignInLink } from "../src/main/auth/pkce";
import { SessionVault } from "../src/main/auth/session-vault";
import type { KeyProtector } from "../src/main/store/key";

const keychain: KeyProtector = {
  isSecure: () => true,
  seal: (secret) => Buffer.from([...secret].reverse().join("")),
  open: (sealed) => [...sealed.toString()].reverse().join(""),
};
const API = "https://api.jalada.example";
const WEB = "https://jalada.example";
// Invented person.
const USER = {
  id: "4b1f0c1e-6f0a-4a57-9a3e-2f2b1d0e9c11",
  email: "amina@example.com",
  display_name: "Amina",
};

const folders: string[] = [];
afterEach(() => {
  for (const made of folders.splice(0))
    rmSync(made, { recursive: true, force: true });
});

function setUp(
  reply = new Response(JSON.stringify({ token: "t0ken", user: USER })),
) {
  const folder = mkdtempSync(join(tmpdir(), "jalada-auth-"));
  folders.push(folder);
  const vault = new SessionVault(join(folder, "session.bin"), keychain);
  const ports = {
    apiOrigin: API,
    webOrigin: WEB,
    vault,
    openInBrowser: vi.fn().mockResolvedValue(undefined),
    fetch: vi.fn().mockResolvedValue(reply),
    changed: vi.fn(),
    forgetRecords: vi.fn(),
  };
  return { auth: new DeviceAuth(ports), ports, vault, folder };
}

/** Starts sign-in and returns the link the browser would send back. */
async function linkBack(
  auth: DeviceAuth,
  opened: ReturnType<typeof vi.fn>,
  code = "one-time",
) {
  await auth.start();
  const page = new URL(opened.mock.calls[0]![0] as string);
  return `jalada://signed-in?code=${code}&state=${page.searchParams.get("state")}`;
}

describe("sign-in request", () => {
  it("sends only the hash of a secret that stays on this computer", () => {
    const request = newSignInRequest();

    expect(request.challenge).toBe(
      createHash("sha256").update(request.verifier).digest("base64url"),
    );
    expect(request.verifier).toMatch(/^[A-Za-z0-9_-]{64}$/);
    expect(request.challenge).toHaveLength(43);
  });

  it("reads only jalada://signed-in links", () => {
    expect(readSignInLink("jalada://signed-in?code=c&state=s")).toEqual({
      code: "c",
      state: "s",
    });
    expect(readSignInLink("jalada://other?code=c&state=s")).toBeNull();
    expect(readSignInLink("https://signed-in?code=c&state=s")).toBeNull();
    expect(readSignInLink("jalada://signed-in?code=c")).toBeNull();
  });
});

describe("device sign-in", () => {
  it("opens the web app's sign-in page with the challenge, never the secret", async () => {
    const { auth, ports } = setUp();
    await auth.start();

    const page = new URL(ports.openInBrowser.mock.calls[0]![0] as string);
    expect(page.origin + page.pathname).toBe(`${WEB}/desktop/sign-in`);
    expect([...page.searchParams.keys()].sort()).toEqual([
      "challenge",
      "state",
    ]);
  });

  it("trades the code and secret for a session, and keeps it sealed", async () => {
    const { auth, ports, folder } = setUp();
    const link = await linkBack(auth, ports.openInBrowser);

    const account = await auth.finish(link);

    expect(account).toEqual({ id: USER.id, email: USER.email, name: "Amina" });
    const sent = JSON.parse(ports.fetch.mock.calls[0]![1].body as string);
    expect(sent.code).toBe("one-time");
    expect(sent.verifier).toMatch(/^[A-Za-z0-9_-]{64}$/);
    expect(
      readFileSync(join(folder, "session.bin")).includes(Buffer.from("t0ken")),
    ).toBe(false);
    expect(ports.changed).toHaveBeenCalledWith(account);
  });

  it("is still signed in after the app starts again", async () => {
    const { auth, ports, vault } = setUp();
    await auth.finish(await linkBack(auth, ports.openInBrowser));

    const restarted = new DeviceAuth({ ...ports, vault });
    expect(restarted.current()).toBeNull();

    expect(restarted.restore()?.email).toBe(USER.email);
    expect(restarted.current()?.email).toBe(USER.email);
    expect(restarted.token()).toBe("t0ken");
  });

  it("ignores a link that does not answer its own request", async () => {
    const { auth, ports } = setUp();
    await auth.start();

    await expect(
      auth.finish("jalada://signed-in?code=c&state=someone-elses"),
    ).rejects.toThrow(SignInFailed);
    expect(ports.fetch).not.toHaveBeenCalled();
  });

  it("uses each request once", async () => {
    const { auth, ports } = setUp();
    const link = await linkBack(auth, ports.openInBrowser);
    await auth.finish(link);

    await expect(auth.finish(link)).rejects.toThrow(SignInFailed);
  });

  it("says so when the server refuses", async () => {
    const { auth, ports } = setUp(new Response("{}", { status: 400 }));

    await expect(
      auth.finish(await linkBack(auth, ports.openInBrowser)),
    ).rejects.toThrow(/did not accept/);
    expect(auth.current()).toBeNull();
  });

  it("signs out on this computer even when the server cannot be reached", async () => {
    const { auth, ports, vault } = setUp();
    await auth.finish(await linkBack(auth, ports.openInBrowser));
    ports.fetch.mockRejectedValue(new TypeError("offline"));

    await auth.signOut();

    expect(auth.current()).toBeNull();
    expect(vault.load()).toBeNull();
    expect(ports.forgetRecords).toHaveBeenCalledWith(USER.id);
    expect(ports.changed).toHaveBeenLastCalledWith(null);
  });
});

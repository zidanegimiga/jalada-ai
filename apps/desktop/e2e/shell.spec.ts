import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  _electron as electron,
  expect,
  test,
  type ElectronApplication,
  type Page,
} from "@playwright/test";
// Run outside Electron, the package gives the path to its own executable.
import electronPath from "electron";

/** The longest the first screen may take from launch, warm, on a CI machine. */
const FIRST_SCREEN_BUDGET_MS = 2500;

let app: ElectronApplication;
let page: Page;
let firstScreenMs: number;

test.beforeAll(async () => {
  const started = Date.now();
  app = await electron.launch({
    executablePath: electronPath as unknown as string,
    // Its own data folder: no clash with a copy someone has open, and no records kept.
    args: [
      ".",
      `--user-data-dir=${mkdtempSync(join(tmpdir(), "jalada-e2e-"))}`,
    ],
    env: { ...process.env, JALADA_API_URL: "http://localhost:8000" },
  });
  page = await app.firstWindow();
  await page.getByRole("heading", { name: /on this computer/ }).waitFor();
  firstScreenMs = Date.now() - started;
  // Tests must never open the real browser: record what the app would hand it instead.
  await app.evaluate(({ shell }) => {
    const handed: string[] = [];
    Object.assign(globalThis, { handedToBrowser: handed });
    shell.openExternal = async (url: string) => {
      handed.push(url);
    };
  });
});

test.afterAll(async () => {
  await app?.close();
});

test("shows its first screen within the start-up budget", () => {
  expect(firstScreenMs).toBeLessThan(FIRST_SCREEN_BUDGET_MS);
});

test("gives the page the bridge and nothing of Node.js", async () => {
  const seen = await page.evaluate(() => ({
    bridge: typeof window.jalada?.connection?.current,
    require: typeof (globalThis as { require?: unknown }).require,
    process: typeof (globalThis as { process?: unknown }).process,
  }));

  expect(seen).toEqual({
    bridge: "function",
    require: "undefined",
    process: "undefined",
  });
});

test("lets the page reach no server, open no window and send no one elsewhere", async () => {
  // An address that does not exist, so even a mistake here could not reach a real site.
  const elsewhere = "https://not-jalada.invalid/";
  const outcome = await page.evaluate(
    async (address) => ({
      fetched: await fetch(address).then(
        () => "reached",
        () => "blocked",
      ),
      opened: window.open(address) === null ? "refused" : "opened",
    }),
    elsewhere,
  );
  const handed = await app.evaluate(
    () => (globalThis as { handedToBrowser?: string[] }).handedToBrowser,
  );

  expect(outcome).toEqual({ fetched: "blocked", opened: "refused" });
  expect(handed).toEqual([]);
});

test("says which server it syncs with, and whether it is online", async () => {
  await expect(
    page.getByText("Syncs with http://localhost:8000"),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText(/Online|Offline/);
});

test("offers sign-in through the browser on a fresh install", async () => {
  await expect(
    page.getByRole("button", { name: "Sign in with your browser" }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/signed-out.png" });
});

test("run from source, signs in through the local web app, with a way back", async () => {
  await page.getByRole("button", { name: "Sign in with your browser" }).click();
  await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible();
  const handed = await app.evaluate(
    () => (globalThis as { handedToBrowser?: string[] }).handedToBrowser,
  );
  expect(handed?.[0]).toMatch(/^http:\/\/localhost:3000\/desktop\/sign-in\?/);

  await page
    .getByLabel("Sign-in link")
    .fill("jalada://signed-in?code=x&state=not-ours");
  await page.getByRole("button", { name: "Finish signing in" }).click();
  await expect(page.getByRole("alert")).toHaveText(/does not answer a sign-in/);

  await page.getByRole("button", { name: "Cancel" }).click();
  await expect(
    page.getByRole("button", { name: "Sign in with your browser" }),
  ).toBeEnabled();
});

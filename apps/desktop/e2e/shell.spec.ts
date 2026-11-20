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

test("lets the page reach no server and open no window itself", async () => {
  const outcome = await page.evaluate(async () => ({
    fetched: await fetch("https://example.com").then(
      () => "reached",
      () => "blocked",
    ),
    opened: window.open("https://example.com") === null ? "refused" : "opened",
  }));

  expect(outcome).toEqual({ fetched: "blocked", opened: "refused" });
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

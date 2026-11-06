import { defineConfig, devices } from "@playwright/test";

/**
 * Journeys through the whole running stack: web app, API, worker, database and storage.
 * Start the stack first (make e2e does both). E2E_BASE_URL points somewhere else.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    // Most people use Jalada AI on a phone.
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
});

import { defineConfig } from "@playwright/test";

// Runs the built app (npm run build first). CI runs it under a virtual screen.
export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
});

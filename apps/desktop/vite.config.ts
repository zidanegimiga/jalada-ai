import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The window: a React app loaded from the app's own files, never from a server.
export default defineConfig({
  root: resolve(__dirname, "src/renderer"),
  base: "./",
  plugins: [react()],
  resolve: { alias: { "@shared": resolve(__dirname, "src/shared") } },
  build: {
    outDir: resolve(__dirname, "dist/renderer"),
    emptyOutDir: true,
    target: "chrome140",
  },
  test: {
    root: __dirname,
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
});

import { resolve } from "node:path";
import { defineConfig } from "vite";

// The bridge between the window and the main process. A sandboxed preload must be one
// CommonJS file that only requires "electron".
export default defineConfig({
  resolve: { alias: { "@shared": resolve(__dirname, "src/shared") } },
  build: {
    outDir: "dist/preload",
    emptyOutDir: true,
    target: "node22",
    ssr: resolve(__dirname, "src/preload/index.ts"),
    rollupOptions: {
      external: ["electron"],
      output: { format: "cjs", entryFileNames: "index.cjs" },
    },
  },
});

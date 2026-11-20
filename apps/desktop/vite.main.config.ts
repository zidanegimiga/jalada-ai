import { builtinModules } from "node:module";
import { resolve } from "node:path";
import { defineConfig } from "vite";

// The main process: Node.js, one CommonJS file Electron starts from.
export default defineConfig({
  resolve: { alias: { "@shared": resolve(__dirname, "src/shared") } },
  build: {
    outDir: "dist/main",
    emptyOutDir: true,
    target: "node22",
    ssr: resolve(__dirname, "src/main/index.ts"),
    rollupOptions: {
      external: [
        "electron",
        // A native module: loaded from node_modules at run time, never bundled.
        "better-sqlite3-multiple-ciphers",
        ...builtinModules,
        ...builtinModules.map((m) => `node:${m}`),
      ],
      output: { format: "cjs", entryFileNames: "index.cjs" },
    },
  },
});

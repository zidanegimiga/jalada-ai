import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Stop next dev from writing an AGENTS.md file into the app.
  agentRules: false,
  // Copy only the files the server needs into .next/standalone, for a small Docker image.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  reactCompiler: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

import type { NextConfig } from "next";

// Where the API runs. Read at build time, so the Docker build passes it in.
const apiUrl = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Read at build time. Netlify sets COMMIT_REF to the commit and CONTEXT to "production"
  // or "deploy-preview". Attached to error reports, so each one names the build it came from.
  env: {
    APP_VERSION: process.env.COMMIT_REF ?? "development",
    APP_ENVIRONMENT: process.env.CONTEXT ?? "development",
    // Netlify sets URL to the site's main address. Links to the sharing image use it.
    SITE_URL: process.env.URL ?? "http://localhost:3000",
    // "on" adds the Ask tab. Set it where the API runs with JALADA_AGENT_ENABLED=true.
    ASSISTANT: process.env.ASSISTANT ?? "off",
  },
  // Stop next dev from writing an AGENTS.md file into the app.
  agentRules: false,
  // Copy only the files the server needs into .next/standalone, for a small Docker image.
  output: "standalone",
  // The browser calls /v1 on this site and Next.js forwards it to the API,
  // so the session cookie stays first-party and no cross-origin setup is needed.
  async rewrites() {
    return [{ source: "/v1/:path*", destination: `${apiUrl}/v1/:path*` }];
  },
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

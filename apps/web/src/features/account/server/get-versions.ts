import "server-only";

import { apiGet } from "@/lib/server-api";

/** A commit hash shortened to the usual 7 characters; other versions as they are. */
export function shortVersion(version: string): string {
  return /^[0-9a-f]{40}$/.test(version) ? version.slice(0, 7) : version;
}

/** The web app's version and the API's, to quote when reporting a problem. */
export async function getVersions(): Promise<{ web: string; api: string }> {
  const health = await apiGet<{ version: string }>("/health");
  return {
    web: shortVersion(process.env.APP_VERSION ?? "development"),
    api: shortVersion(health?.version ?? "unknown"),
  };
}

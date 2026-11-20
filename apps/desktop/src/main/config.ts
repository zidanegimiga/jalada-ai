/** Where the desktop app finds its server and the web app, read once at start-up. */
export type DesktopConfig = { apiOrigin: string; webOrigin: string };

/** The live service, for packaged builds. */
const LIVE = {
  api: "https://jalada-api.onrender.com",
  web: "https://jalada-ai.netlify.app",
};
/** The local stack (`make up`), for the app run from source with `npm start`. */
const LOCAL = { api: "http://localhost:8000", web: "http://localhost:3000" };

/** True when Electron runs the app from source rather than as a packaged build. */
function runFromSource(): boolean {
  return (process as { defaultApp?: boolean }).defaultApp === true;
}
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

/**
 * An origin from an address setting. Only HTTPS is accepted, except on this computer for
 * development, so records and sign-in codes never travel unencrypted.
 */
function origin(name: string, raw: string): string {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error(`${name} is not an address: ${raw}`);
  }
  const local = LOCAL_HOSTS.has(url.hostname);
  if (url.protocol !== "https:" && !(local && url.protocol === "http:")) {
    throw new Error(`${name} must use https, except on localhost.`);
  }
  return url.origin;
}

/**
 * The API from JALADA_API_URL and the web app from JALADA_WEB_URL. Without them, a packaged
 * build uses the live service and the app run from source uses the local stack, so trying
 * a change never sends someone to a live site that does not have it yet.
 */
export function loadConfig(
  env: Record<string, string | undefined>,
  fromSource: boolean = runFromSource(),
): DesktopConfig {
  const defaults = fromSource ? LOCAL : LIVE;
  return {
    apiOrigin: origin(
      "JALADA_API_URL",
      env.JALADA_API_URL?.trim() || defaults.api,
    ),
    webOrigin: origin(
      "JALADA_WEB_URL",
      env.JALADA_WEB_URL?.trim() || defaults.web,
    ),
  };
}

/** Where the desktop app finds its server and the web app, read once at start-up. */
export type DesktopConfig = { apiOrigin: string; webOrigin: string };

const DEFAULT_API = "https://jalada-api.onrender.com";
const DEFAULT_WEB = "https://jalada-ai.netlify.app";
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

/** The API from JALADA_API_URL and the web app from JALADA_WEB_URL, or the live ones. */
export function loadConfig(
  env: Record<string, string | undefined>,
): DesktopConfig {
  return {
    apiOrigin: origin(
      "JALADA_API_URL",
      env.JALADA_API_URL?.trim() || DEFAULT_API,
    ),
    webOrigin: origin(
      "JALADA_WEB_URL",
      env.JALADA_WEB_URL?.trim() || DEFAULT_WEB,
    ),
  };
}

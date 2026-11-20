/** Where the desktop app finds its server, read once at start-up. */
export type DesktopConfig = { apiOrigin: string };

const DEFAULT_API = "https://jalada-api.onrender.com";
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

/**
 * The API origin from JALADA_API_URL, or the live one. Only HTTPS is accepted, except on this
 * computer for development, so records never travel unencrypted.
 */
export function loadConfig(
  env: Record<string, string | undefined>,
): DesktopConfig {
  const raw = env.JALADA_API_URL?.trim() || DEFAULT_API;
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error(`JALADA_API_URL is not an address: ${raw}`);
  }
  const local = LOCAL_HOSTS.has(url.hostname);
  if (url.protocol !== "https:" && !(local && url.protocol === "http:")) {
    throw new Error("JALADA_API_URL must use https, except on localhost.");
  }
  return { apiOrigin: url.origin };
}

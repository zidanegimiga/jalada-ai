/** Pages anyone can see. Only these are ever kept on the device (decision 0028). */
export const PUBLIC_PAGES = [
  "/offline",
  "/welcome",
  "/signin",
  "/signup",
  "/privacy",
];

/** Files kept when the service worker installs, beside the offline page and its own files. */
const PRECACHE = ["/mark.webp", "/logo.webp", "/icons/icon-192.png"];

/** Tells the waiting version to take over, once the person agrees to reload. */
export const ACTIVATE_UPDATE = "activate-update";

/**
 * The service worker's script, with this build's version in it so browsers notice a new
 * build. It is plain JavaScript, since the browser runs it as it is.
 *
 * - Build files and icons: from the device first; their names change with their content.
 * - Pages: from the network. Public pages are kept as a fallback; any other page, offline,
 *   shows /offline. Signed-in pages are never kept.
 * - Anything else, /v1 calls, writes and other websites: left to the browser, untouched.
 */
export function serviceWorkerScript(version: string): string {
  return `"use strict";
const VERSION = ${JSON.stringify(version)};
const PAGES = "jalada-pages-" + VERSION;
const FILES = "jalada-files";
const PUBLIC_PAGES = ${JSON.stringify(PUBLIC_PAGES)};
const PRECACHE = ${JSON.stringify(PRECACHE)};

function ruleFor(request) {
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return "browser";
  if (url.pathname.startsWith("/v1/")) return "browser";
  const file =
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    PRECACHE.includes(url.pathname);
  if (file) return "files";
  if (request.mode === "navigate") return "page";
  return "browser";
}

async function fromFilesFirst(request) {
  const cache = await caches.open(FILES);
  const kept = await cache.match(request);
  if (kept) return kept;
  const response = await fetch(request);
  if (response.ok) cache.put(request, response.clone());
  return response;
}

async function fromNetworkFirst(request) {
  const cache = await caches.open(PAGES);
  const path = new URL(request.url).pathname;
  const isPublic = PUBLIC_PAGES.includes(path);
  try {
    const response = await fetch(request);
    if (isPublic && response.ok && !response.redirected) cache.put(path, response.clone());
    return response;
  } catch (error) {
    return (isPublic && (await cache.match(path))) || (await cache.match("/offline")) || Response.error();
  }
}

// The offline page, and every script and style it links to, so it works even when it was
// never opened before the connection dropped.
async function keepOfflinePage() {
  const response = await fetch("/offline");
  const html = await response.clone().text();
  const linked = Array.from(new Set(html.match(/\\/_next\\/static\\/[^"'\\\\\\s)]+/g) || []));
  await (await caches.open(PAGES)).put("/offline", response);
  await (await caches.open(FILES)).addAll([...PRECACHE, ...linked]);
}

self.addEventListener("install", (event) => {
  event.waitUntil(keepOfflinePage());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((name) => name.startsWith("jalada-pages-") && name !== PAGES)
            .map((name) => caches.delete(name)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  if (event.data === ${JSON.stringify(ACTIVATE_UPDATE)}) self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const rule = ruleFor(event.request);
  if (rule === "files") event.respondWith(fromFilesFirst(event.request));
  if (rule === "page") event.respondWith(fromNetworkFirst(event.request));
});
`;
}

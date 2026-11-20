import { serviceWorkerScript } from "@/features/offline/service-worker";

/**
 * The service worker, at the site's root so it can look after every page. Browsers check
 * it on each visit; it is never kept by caches, so a new build is noticed straight away.
 */
export function GET() {
  return new Response(serviceWorkerScript(process.env.APP_VERSION ?? "dev"), {
    headers: {
      "Content-Type": "text/javascript; charset=utf-8",
      "Cache-Control": "no-cache, no-store, must-revalidate",
    },
  });
}

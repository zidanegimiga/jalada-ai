"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/shared/components/Button";

import { ACTIVATE_UPDATE } from "../../service-worker";

/**
 * Registers the service worker in production builds (decision 0028), and offers to reload
 * when a new version of the app has downloaded. Reloading is the person's choice, so a
 * half-filled form is never swapped for new code under them.
 */
export function ServiceWorkerSetup({ enabled }: { enabled: boolean }) {
  const [waiting, setWaiting] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    if (!enabled || !("serviceWorker" in navigator)) return;
    const workers = navigator.serviceWorker;
    workers.register("/sw.js").then((registration) => {
      if (registration.waiting && workers.controller) {
        setWaiting(registration.waiting);
      }
      registration.addEventListener("updatefound", () => {
        const next = registration.installing;
        next?.addEventListener("statechange", () => {
          // With no controller this is the first install, not an update.
          if (next.state === "installed" && workers.controller) {
            setWaiting(next);
          }
        });
      });
    });
  }, [enabled]);

  /** Lets the new version take over, then reloads into it. Only ever on the person's word:
   * the first install also changes the controller, and must not reload the page. */
  function update(next: ServiceWorker) {
    navigator.serviceWorker.addEventListener(
      "controllerchange",
      () => window.location.reload(),
      { once: true },
    );
    next.postMessage(ACTIVATE_UPDATE);
  }

  if (!waiting) return null;
  return (
    <div
      role="status"
      className="fixed inset-x-gutter bottom-28 z-50 mx-auto flex max-w-page items-center gap-3 rounded-card bg-foreground p-3 pl-5 text-background shadow-overlay lg:bottom-6"
    >
      <p className="flex-1">A new version of Jalada AI is ready.</p>
      <Button size="sm" onClick={() => update(waiting)}>
        <RefreshCw aria-hidden="true" />
        Reload
      </Button>
    </div>
  );
}

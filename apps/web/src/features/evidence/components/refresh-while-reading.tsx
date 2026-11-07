"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getEvidence, isStillReading } from "../api";

/** Waits between checks: quick at first, then every 10 seconds. */
export const CHECK_DELAYS_MS = [2_000, 2_000, 3_000, 5_000, 8_000];
const LATER_DELAY_MS = 10_000;
/** Stop after this long; a reload picks up anything slower. */
export const GIVE_UP_AFTER_MS = 120_000;

/**
 * Checks evidence the worker is still reading, and refreshes the page once any of it is
 * done, so the list, the month and the items to check all update. Renders nothing.
 */
export function RefreshWhileReading({ waiting }: { waiting: string[] }) {
  const router = useRouter();
  const key = waiting.join(",");

  useEffect(() => {
    if (!key) return;
    const ids = key.split(",");
    let timer: ReturnType<typeof setTimeout>;
    let checks = 0;
    let waited = 0;

    function schedule() {
      const delay = CHECK_DELAYS_MS[checks] ?? LATER_DELAY_MS;
      if (waited + delay > GIVE_UP_AFTER_MS) return;
      waited += delay;
      timer = setTimeout(check, delay);
    }

    async function check() {
      checks += 1;
      const latest = await Promise.all(ids.map(getEvidence));
      const done = latest.some(
        (item) => item !== null && !isStillReading(item),
      );
      if (done) router.refresh();
      else schedule();
    }

    schedule();
    return () => clearTimeout(timer);
  }, [key, router]);

  return null;
}

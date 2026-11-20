import type { Metadata } from "next";
import { WifiOff } from "lucide-react";

import { ReloadWhenOnline } from "@/features/offline/components/ReloadWhenOnline";
import { Brand } from "@/shared/components/Brand";

export const metadata: Metadata = { title: "Offline · Jalada AI" };

/**
 * What the installed app shows when a page cannot load. The service worker keeps it on the
 * device (decision 0028), so it holds nothing personal.
 */
export default function OfflinePage() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-page flex-col gap-section px-gutter py-10">
      <Brand />
      <div className="flex flex-1 flex-col items-start justify-center gap-4">
        <span className="grid size-16 place-items-center rounded-card bg-secondary text-secondary-foreground">
          <WifiOff aria-hidden="true" className="size-icon-lg" />
        </span>
        <h1 className="text-display">You are offline</h1>
        <p className="text-lead text-muted-foreground">
          Your records are safe. Jalada AI needs a connection to show them and
          to save new ones. This page opens your app again as soon as you are
          back online.
        </p>
        <ReloadWhenOnline />
      </div>
    </main>
  );
}

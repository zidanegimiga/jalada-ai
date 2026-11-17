import { Suspense } from "react";

import { AccountNotice } from "@/features/auth/components/AccountNotice";
import { isStillReading } from "@/features/evidence/api/evidence.api";
import { CapturePanel } from "@/features/evidence/components/CapturePanel";
import { EvidenceList } from "@/features/evidence/components/EvidenceList";
import { EvidenceListSkeleton } from "@/features/evidence/components/EvidenceListSkeleton";
import { RefreshWhileReading } from "@/features/evidence/components/RefreshWhileReading";
import { getRecentEvidence } from "@/features/evidence/server/get-recent-evidence";
import { getTelegramStatus } from "@/features/telegram/server/get-telegram-status";

import { HomeOverview, HomeOverviewSkeleton } from "./_components/HomeOverview";

async function RecentEvidence() {
  const [items, telegram] = await Promise.all([
    getRecentEvidence(),
    getTelegramStatus(),
  ]);
  const state = !telegram.available
    ? "off"
    : telegram.linked
      ? "linked"
      : "unlinked";
  return (
    <>
      <EvidenceList items={items} telegram={state} />
      <RefreshWhileReading
        waiting={items.filter(isStillReading).map((item) => item.id)}
      />
    </>
  );
}

export default function Home() {
  return (
    <>
      <Suspense>
        <AccountNotice />
      </Suspense>
      <Suspense fallback={<HomeOverviewSkeleton />}>
        <HomeOverview />
      </Suspense>
      <CapturePanel />
      <section aria-labelledby="recent-heading" className="flex flex-col gap-3">
        <h2 id="recent-heading" className="text-title">
          Recent
        </h2>
        <Suspense fallback={<EvidenceListSkeleton />}>
          <RecentEvidence />
        </Suspense>
      </section>
    </>
  );
}

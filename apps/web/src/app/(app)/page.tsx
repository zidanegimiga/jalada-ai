import { connection } from "next/server";
import { Suspense } from "react";

import { AccountNotice } from "@/features/auth/components/AccountNotice";
import { ConsentChoice } from "@/features/consent/components/ConsentChoice";
import { getModelConsent } from "@/features/consent/server/get-model-consent";
import { isStillReading } from "@/features/evidence/api/evidence.api";
import { CapturePanel } from "@/features/evidence/components/CapturePanel";
import { EvidenceList } from "@/features/evidence/components/EvidenceList";
import { EvidenceListSkeleton } from "@/features/evidence/components/EvidenceListSkeleton";
import { RefreshWhileReading } from "@/features/evidence/components/RefreshWhileReading";
import { getRecentEvidence } from "@/features/evidence/server/get-recent-evidence";
import { recentPoints } from "@/features/ledger/charts";
import {
  MoneyChartCard,
  MoneyChartCardSkeleton,
} from "@/features/ledger/components/MoneyChartCard";
import { getYear } from "@/features/ledger/server/queries";
import { getTelegramStatus } from "@/features/telegram/server/get-telegram-status";
import { nairobiMonth } from "@/shared/format/nairobi";

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

/** Asks once whether a model may read the person's records, when one is set up. */
async function HomeConsent() {
  return <ConsentChoice consent={await getModelConsent()} place="home" />;
}

/** The last six months up to this one, which may reach back into last year. */
async function RecentMonths() {
  await connection();
  const { year, month } = nairobiMonth();
  const [thisYear, lastYear] = await Promise.all([
    getYear(year),
    month < 6 ? getYear(year - 1) : Promise.resolve([]),
  ]);
  return (
    <MoneyChartCard
      tab="Last 6 months"
      points={recentPoints(year, month, thisYear, lastYear)}
    />
  );
}

/** One column on a phone; on a wide screen the money on the left, adding evidence on the right. */
export default function Home() {
  return (
    <>
      <Suspense>
        <AccountNotice />
      </Suspense>
      <Suspense>
        <HomeConsent />
      </Suspense>
      <div className="flex flex-col gap-section xl:grid xl:grid-cols-2 xl:items-start">
        <div className="flex flex-col gap-section">
          <Suspense fallback={<HomeOverviewSkeleton />}>
            <HomeOverview />
          </Suspense>
          <Suspense fallback={<MoneyChartCardSkeleton tab="Last 6 months" />}>
            <RecentMonths />
          </Suspense>
        </div>
        <div className="flex flex-col gap-section">
          <CapturePanel />
          <section
            aria-labelledby="recent-heading"
            className="flex flex-col gap-3"
          >
            <h2 id="recent-heading" className="text-title">
              Recent
            </h2>
            <Suspense fallback={<EvidenceListSkeleton />}>
              <RecentEvidence />
            </Suspense>
          </section>
        </div>
      </div>
    </>
  );
}

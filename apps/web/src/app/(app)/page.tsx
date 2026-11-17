import Link from "next/link";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { Spinner } from "@/shared/components/Spinner";
import { AccountNotice } from "@/features/auth/components/AccountNotice";
import { getCurrentUser } from "@/features/auth/server/get-current-user";
import { CapturePanel } from "@/features/evidence/components/CapturePanel";
import { isStillReading } from "@/features/evidence/api/evidence.api";
import { EvidenceList } from "@/features/evidence/components/EvidenceList";
import { RefreshWhileReading } from "@/features/evidence/components/RefreshWhileReading";
import { getRecentEvidence } from "@/features/evidence/server/get-recent-evidence";
import { MonthCard } from "@/features/ledger/components/MonthCard";
import { getMonth } from "@/features/ledger/server/queries";
import { getReviewQueue } from "@/features/review/server/queries";
import { TelegramCard } from "@/features/telegram/components/TelegramCard";
import { getTelegramStatus } from "@/features/telegram/server/get-telegram-status";

/** Today's year and month in Kenya, whatever time zone the server runs in. */
function nairobiMonth(): [number, number] {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "2-digit",
  }).formatToParts(new Date());
  const value = (type: string) =>
    Number(parts.find((part) => part.type === type)?.value);
  return [value("year"), value("month")];
}

async function Overview() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  const [year, month] = nairobiMonth();
  const [summary, waiting] = await Promise.all([
    getMonth(year, month),
    getReviewQueue(),
  ]);
  return (
    <>
      <h1 className="text-display">Hello, {user.display_name}</h1>
      {summary && <MonthCard year={year} month={summary} />}
      {waiting.length > 0 && (
        <Link
          href="/review"
          className="rounded-card bg-secondary px-5 py-4 text-lead font-medium text-secondary-foreground"
        >
          {waiting.length === 1
            ? "1 item to check"
            : `${waiting.length} items to check`}{" "}
          →
        </Link>
      )}
    </>
  );
}

async function Telegram() {
  const status = await getTelegramStatus();
  return <TelegramCard available={status.available} linked={status.linked} />;
}

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
      <Suspense fallback={<div className="h-40" />}>
        <Overview />
      </Suspense>
      <CapturePanel />
      <Suspense>
        <Telegram />
      </Suspense>
      <section aria-labelledby="recent-heading" className="flex flex-col gap-3">
        <h2 id="recent-heading" className="text-title">
          Recent
        </h2>
        <Suspense fallback={<Spinner />}>
          <RecentEvidence />
        </Suspense>
      </section>
    </>
  );
}

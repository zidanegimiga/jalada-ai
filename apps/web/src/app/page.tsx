import Link from "next/link";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { Spinner } from "@/components/ui/spinner";
import { AccountNotice } from "@/features/auth/components/account-notice";
import { getCurrentUser } from "@/features/auth/server/get-current-user";
import { CapturePanel } from "@/features/evidence/components/capture-panel";
import { EvidenceList } from "@/features/evidence/components/evidence-list";
import { getRecentEvidence } from "@/features/evidence/server/get-recent-evidence";
import { MonthCard } from "@/features/ledger/components/month-card";
import { getMonth } from "@/features/ledger/server/queries";
import { getReviewQueue } from "@/features/review/server/queries";
import { TelegramCard } from "@/features/telegram/components/telegram-card";
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
      <h1 className="text-4xl font-bold">Hello, {user.display_name}</h1>
      {summary && <MonthCard year={year} month={summary} />}
      {waiting.length > 0 && (
        <Link
          href="/review"
          className="rounded-3xl bg-secondary px-5 py-4 text-lg font-medium text-secondary-foreground"
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
  return <EvidenceList items={await getRecentEvidence()} />;
}

export default function Home() {
  return (
    <AppShell>
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
        <h2 id="recent-heading" className="text-xl font-bold">
          Recent
        </h2>
        <Suspense fallback={<Spinner />}>
          <RecentEvidence />
        </Suspense>
      </section>
    </AppShell>
  );
}

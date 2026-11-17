import { ArrowRight, CheckCheck } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

import { getCurrentUser } from "@/features/auth/server/get-current-user";
import { MonthCard } from "@/features/ledger/components/MonthCard";
import { MonthCardSkeleton } from "@/features/ledger/components/MonthCardSkeleton";
import { getMonth } from "@/features/ledger/server/queries";
import type { Month } from "@/features/ledger/types";
import { getReviewQueue } from "@/features/review/server/queries";
import { SkeletonText } from "@/shared/components/Skeleton";
import { nairobiMonth } from "@/shared/format/nairobi";

function emptyMonth(month: number): Month {
  return {
    month,
    in_business_cents: 0,
    in_personal_cents: 0,
    out_business_cents: 0,
    out_personal_cents: 0,
  };
}

const ROW =
  "flex min-h-14 items-center gap-3 rounded-card px-5 text-lead font-medium";

/** One line, the same height whether or not anything waits, so the page never moves. */
function Waiting({ count }: { count: number }) {
  if (count === 0) {
    return (
      <p className={`${ROW} bg-muted text-muted-foreground`}>
        <CheckCheck aria-hidden="true" className="size-icon" />
        Nothing waiting to check
      </p>
    );
  }
  return (
    <Link
      href="/review"
      className={`${ROW} group bg-secondary text-secondary-foreground`}
    >
      {count === 1 ? "1 item to check" : `${count} items to check`}
      <ArrowRight
        aria-hidden="true"
        className="ml-auto size-icon transition-transform group-hover:translate-x-1"
      />
    </Link>
  );
}

/** The greeting, this month's totals and what waits on To check. */
export async function HomeOverview() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  const { year, month } = nairobiMonth();
  const [summary, waiting] = await Promise.all([
    getMonth(year, month),
    getReviewQueue(),
  ]);
  const firstName = user.display_name.trim().split(/\s+/)[0];
  return (
    <>
      <h1 className="truncate text-display">Hello, {firstName}</h1>
      <MonthCard year={year} month={summary ?? emptyMonth(month)} />
      <Waiting count={waiting.length} />
    </>
  );
}

export function HomeOverviewSkeleton() {
  return (
    <>
      <h1 className="text-display">
        <SkeletonText className="w-56" />
      </h1>
      <MonthCardSkeleton />
      <p className={`${ROW} bg-muted`}>
        <SkeletonText className="w-44" />
      </p>
    </>
  );
}

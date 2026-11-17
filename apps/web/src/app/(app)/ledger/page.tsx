import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { buttonVariants } from "@/shared/components/Button";
import { ExportCard } from "@/features/export/components/ExportCard";
import { ExportCardSkeleton } from "@/features/export/components/ExportCardSkeleton";
import { defaultExportYear } from "@/features/export/default-year";
import {
  LedgerFilters,
  LedgerFiltersSkeleton,
} from "@/features/ledger/components/LedgerFilters";
import { LedgerList } from "@/features/ledger/components/LedgerList";
import { LedgerListSkeleton } from "@/features/ledger/components/LedgerListSkeleton";
import { topCategories, yearPoints } from "@/features/ledger/charts";
import {
  CategoriesCard,
  CategoriesCardSkeleton,
} from "@/features/ledger/components/CategoriesCard";
import {
  MoneyChartCard,
  MoneyChartCardSkeleton,
} from "@/features/ledger/components/MoneyChartCard";
import {
  getCategoryTotals,
  getLedger,
  getYear,
} from "@/features/ledger/server/queries";
import type { LedgerQuery } from "@/features/ledger/types";
import { nairobiMonth } from "@/shared/format/nairobi";

/** Today's year, read per request rather than frozen in at build time. */
async function Export() {
  await connection();
  const currentYear = new Date().getFullYear();
  const lastYear = await getYear(currentYear - 1);
  return (
    <ExportCard
      currentYear={currentYear}
      defaultYear={defaultExportYear(currentYear, lastYear)}
    />
  );
}

async function Entries({ query }: { query: Promise<LedgerQuery> }) {
  const filters = await query;
  const page = await getLedger(filters);
  const next = new URLSearchParams({
    ...filters,
    cursor: page.next_cursor ?? "",
  });
  return (
    <>
      <LedgerList
        entries={page.items}
        filtered={Boolean(
          filters.q || filters.month || filters.direction || filters.purpose,
        )}
        search={filters.q}
      />
      {page.next_cursor && (
        <Link
          href={`/ledger?${next}`}
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          Show older
        </Link>
      )}
    </>
  );
}

/** This year's months, read per request so the year is always the current one. */
async function YearChart() {
  await connection();
  const { year, month } = nairobiMonth();
  return (
    <MoneyChartCard
      tab="This year"
      points={yearPoints(year, await getYear(year))}
      current={month - 1}
    />
  );
}

/** The month being filtered, or this whole year: its first and last days and a name. */
function period(query: LedgerQuery, year: number) {
  const match = /^(\d{4})-(\d{2})$/.exec(query.month ?? "");
  if (!match)
    return { from: `${year}-01-01`, to: `${year}-12-31`, tab: "This year" };
  const [y, m] = [Number(match[1]), Number(match[2])];
  const last = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const name = new Intl.DateTimeFormat("en-KE", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(y, m - 1, 1)));
  return { from: `${query.month}-01`, to: `${query.month}-${last}`, tab: name };
}

async function Categories({ query }: { query: Promise<LedgerQuery> }) {
  await connection();
  const { from, to, tab } = period(await query, nairobiMonth().year);
  const totals = await getCategoryTotals(from, to);
  return (
    <CategoriesCard
      tab={tab}
      slices={{
        in: topCategories(totals, "in"),
        out: topCategories(totals, "out"),
      }}
    />
  );
}

/**
 * On a phone: the year, the filters and entries, then categories and the download. On a
 * wide screen the entries take the left column and the rest sit beside them.
 */
export default function LedgerPage({ searchParams }: PageProps<"/ledger">) {
  const query = searchParams as Promise<LedgerQuery>;
  return (
    <>
      <h1 className="text-display">Ledger</h1>
      <div className="flex flex-col gap-section xl:grid xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] xl:items-start">
        <div className="contents xl:flex xl:flex-col xl:gap-section">
          <div className="order-2 xl:order-none">
            <Suspense fallback={<LedgerFiltersSkeleton />}>
              <LedgerFilters />
            </Suspense>
          </div>
          <div className="order-3 flex flex-col gap-section xl:order-none">
            <Suspense fallback={<LedgerListSkeleton />}>
              <Entries query={query} />
            </Suspense>
          </div>
        </div>
        <div className="contents xl:sticky xl:top-8 xl:flex xl:flex-col xl:gap-section">
          <div className="order-1 xl:order-none">
            <Suspense fallback={<MoneyChartCardSkeleton tab="This year" />}>
              <YearChart />
            </Suspense>
          </div>
          <div className="order-4 xl:order-none">
            <Suspense fallback={<CategoriesCardSkeleton tab="This year" />}>
              <Categories query={query} />
            </Suspense>
          </div>
          <div className="order-5 xl:order-none">
            <Suspense fallback={<ExportCardSkeleton />}>
              <Export />
            </Suspense>
          </div>
        </div>
      </div>
    </>
  );
}

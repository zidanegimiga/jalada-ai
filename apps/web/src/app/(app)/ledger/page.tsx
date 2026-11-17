import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { Spinner } from "@/shared/components/Spinner";
import { buttonVariants } from "@/shared/components/Button";
import { ExportCard } from "@/features/export/components/ExportCard";
import { defaultExportYear } from "@/features/export/default-year";
import { LedgerFilters } from "@/features/ledger/components/LedgerFilters";
import { LedgerList } from "@/features/ledger/components/LedgerList";
import { getLedger, getYear } from "@/features/ledger/server/queries";
import type { LedgerQuery } from "@/features/ledger/types";

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
          filters.month || filters.direction || filters.purpose,
        )}
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

export default function LedgerPage({ searchParams }: PageProps<"/ledger">) {
  return (
    <>
      <h1 className="text-display">Ledger</h1>
      <Suspense fallback={<div className="h-56" />}>
        <Export />
      </Suspense>
      <Suspense>
        <LedgerFilters />
      </Suspense>
      <Suspense fallback={<Spinner />}>
        <Entries query={searchParams as Promise<LedgerQuery>} />
      </Suspense>
    </>
  );
}

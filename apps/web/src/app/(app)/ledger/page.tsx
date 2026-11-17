import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { AppShell } from "@/app/(app)/_components/AppShell";
import { Spinner } from "@/shared/components/Spinner";
import { buttonVariants } from "@/shared/components/Button";
import { ExportCard } from "@/features/export/components/ExportCard";
import { LedgerFilters } from "@/features/ledger/components/LedgerFilters";
import { LedgerList } from "@/features/ledger/components/LedgerList";
import { getLedger } from "@/features/ledger/server/queries";
import type { LedgerQuery } from "@/features/ledger/types";

/** Today's year, read per request rather than frozen in at build time. */
async function Export() {
  await connection();
  return <ExportCard currentYear={new Date().getFullYear()} />;
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
    <AppShell>
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
    </AppShell>
  );
}

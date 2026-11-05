import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { buttonVariants } from "@/components/ui/button";
import { ExportCard } from "@/features/export/components/export-card";
import { LedgerFilters } from "@/features/ledger/components/ledger-filters";
import { LedgerList } from "@/features/ledger/components/ledger-list";
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
      <LedgerList entries={page.items} />
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
      <h1 className="text-4xl font-bold">Ledger</h1>
      <Suspense fallback={<div className="h-56" />}>
        <Export />
      </Suspense>
      <Suspense>
        <LedgerFilters />
      </Suspense>
      <Suspense fallback={<p className="text-muted-foreground">Loading...</p>}>
        <Entries query={searchParams as Promise<LedgerQuery>} />
      </Suspense>
    </AppShell>
  );
}

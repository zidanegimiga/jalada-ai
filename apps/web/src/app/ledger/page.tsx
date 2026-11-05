import Link from "next/link";
import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { buttonVariants } from "@/components/ui/button";
import { LedgerFilters } from "@/features/ledger/components/ledger-filters";
import { LedgerList } from "@/features/ledger/components/ledger-list";
import { getLedger } from "@/features/ledger/server/queries";
import type { LedgerQuery } from "@/features/ledger/types";

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
      <Suspense>
        <LedgerFilters />
      </Suspense>
      <Suspense fallback={<p className="text-muted-foreground">Loading...</p>}>
        <Entries query={searchParams as Promise<LedgerQuery>} />
      </Suspense>
    </AppShell>
  );
}

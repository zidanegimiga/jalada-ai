import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { EntryDetailSkeleton } from "@/features/ledger/components/EntryDetailSkeleton";
import { EntryEvidence } from "@/features/ledger/components/EntryEvidence";
import { EntryFacts } from "@/features/ledger/components/EntryFacts";
import { EntryHeader } from "@/features/ledger/components/EntryHeader";
import { EntryHistory } from "@/features/ledger/components/EntryHistory";
import { getEntry } from "@/features/ledger/server/queries";
import { EditEntry } from "@/features/review/components/EditEntry";
import { getCategories } from "@/features/review/server/queries";

async function Entry({ params }: { params: Promise<{ id: string }> }) {
  const [detail, categories] = await Promise.all([
    getEntry((await params).id),
    getCategories(),
  ]);
  if (!detail) notFound();
  return (
    <>
      <EntryHeader entry={detail.entry} />
      <EntryFacts entry={detail.entry} />
      <EditEntry entry={detail.entry} categories={categories} />
      <EntryEvidence evidence={detail.evidence} />
      <EntryHistory history={detail.history} />
    </>
  );
}

/** One payment: what it was, the evidence behind it, and what happened to it. */
export default function EntryPage({
  params,
}: PageProps<"/ledger/entries/[id]">) {
  return (
    <div className="mx-auto flex w-full max-w-content flex-col gap-section">
      <Link
        href="/ledger"
        className="inline-flex min-h-tap w-fit items-center gap-2 font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft aria-hidden="true" className="size-icon" />
        Ledger
      </Link>
      <Suspense fallback={<EntryDetailSkeleton />}>
        <Entry params={params} />
      </Suspense>
    </div>
  );
}

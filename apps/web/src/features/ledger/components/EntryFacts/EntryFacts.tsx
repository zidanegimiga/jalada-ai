import Link from "next/link";
import type { ReactNode } from "react";

import type { Entry } from "@/features/review/types";

const PURPOSES = {
  business: "Business",
  personal: "Personal",
  unsure: "Not decided",
} as const;

function Fact({ term, children }: { term: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-3">
      <dt className="text-muted-foreground">{term}</dt>
      <dd className="text-right font-medium">{children}</dd>
    </div>
  );
}

/** What the payment was for, and where it is counted. */
export function EntryFacts({ entry }: { entry: Entry }) {
  return (
    <section
      aria-labelledby="facts-heading"
      className="rounded-card border border-border bg-card px-card"
    >
      <h2 id="facts-heading" className="sr-only">
        Details
      </h2>
      <dl className="divide-y divide-border">
        <Fact term="What for">{entry.category_name ?? "Not categorised"}</Fact>
        <Fact term="Business or personal">{PURPOSES[entry.purpose]}</Fact>
        {entry.linked_certificate_id && (
          <Fact term="Counted on">
            <Link
              href={`/ledger/certificates/${entry.linked_certificate_id}`}
              className="inline-flex min-h-tap items-center underline underline-offset-4"
            >
              Its withholding certificate
            </Link>
          </Fact>
        )}
      </dl>
    </section>
  );
}

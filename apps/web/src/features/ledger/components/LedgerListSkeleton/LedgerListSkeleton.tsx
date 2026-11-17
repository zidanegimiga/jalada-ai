import { SkeletonText } from "@/shared/components/Skeleton";
import { cn } from "@/shared/styles/cn";

import { LEDGER_COLUMNS } from "../LedgerRow";

/** LedgerList's shape while entries load: a month heading and rows of the same height. */
export function LedgerListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div
      aria-busy="true"
      aria-label="Loading entries"
      className="flex flex-col gap-2"
    >
      <p className="px-1 font-mono text-tiny">
        <SkeletonText className="w-28" />
      </p>
      <div className="overflow-hidden rounded-card border border-border bg-card">
        <div
          className={cn(
            LEDGER_COLUMNS,
            "hidden border-b border-border bg-muted py-2.5 font-mono text-tiny lg:grid",
          )}
        >
          <SkeletonText className="w-10" />
        </div>
        <ul className="flex flex-col divide-y divide-border">
          {Array.from({ length: rows }, (_, index) => (
            <li key={index} className={cn(LEDGER_COLUMNS, "py-4 lg:py-3.5")}>
              <span className="hidden text-small lg:block">
                <SkeletonText className="w-20" />
              </span>
              <span className="font-medium">
                <SkeletonText className="w-36" />
              </span>
              <span className="hidden text-small lg:block">
                <SkeletonText className="w-28" />
              </span>
              <span className="justify-self-end font-bold">
                <SkeletonText className="w-20" />
              </span>
              <span className="col-span-2 text-small lg:hidden">
                <SkeletonText className="w-48" />
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

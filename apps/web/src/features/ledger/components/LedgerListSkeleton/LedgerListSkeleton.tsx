import { SkeletonText } from "@/shared/components/Skeleton";

/** Rows shaped like LedgerList's while entries load. */
export function LedgerListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <ul
      aria-busy="true"
      aria-label="Loading entries"
      className="flex flex-col divide-y divide-border rounded-card border border-border bg-card"
    >
      {Array.from({ length: rows }, (_, index) => (
        <li
          key={index}
          className="flex items-center justify-between gap-3 px-4 py-4"
        >
          <div className="flex min-w-0 flex-col">
            <span className="font-medium">
              <SkeletonText className="w-36" />
            </span>
            <span className="text-small">
              <SkeletonText className="w-48" />
            </span>
          </div>
          <span className="font-bold">
            <SkeletonText className="w-20" />
          </span>
        </li>
      ))}
    </ul>
  );
}

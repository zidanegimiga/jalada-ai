import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

/** Rows shaped like EvidenceList's while recent evidence loads. */
export function EvidenceListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <ul
      aria-busy="true"
      aria-label="Loading recent evidence"
      className="flex flex-col divide-y divide-border rounded-card border border-border bg-card"
    >
      {Array.from({ length: rows }, (_, index) => (
        <li key={index} className="flex items-center gap-4 px-4 py-4">
          <Skeleton className="size-11 shrink-0 rounded-inset" />
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="font-medium">
              <SkeletonText className="w-20" />
            </span>
            <span className="text-small">
              <SkeletonText className="w-36" />
            </span>
          </div>
          <div className="flex flex-col items-end gap-1 text-small">
            <span>
              <SkeletonText className="w-20" />
            </span>
            <span className="inline-flex min-h-tap items-center">
              <SkeletonText className="w-10" />
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

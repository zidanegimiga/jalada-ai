import { FolderCard } from "@/shared/components/FolderCard";
import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

/** The detail page's shape while the payment loads. */
export function EntryDetailSkeleton() {
  return (
    <>
      <FolderCard tab="Payment" aria-busy="true" className="gap-3">
        <p className="text-display">
          <SkeletonText className="w-48 bg-current opacity-20" />
        </p>
        <p className="text-total">
          <SkeletonText className="w-40 bg-current opacity-20" />
        </p>
        <p>
          <SkeletonText className="w-28 bg-current opacity-20" />
        </p>
      </FolderCard>
      <Skeleton className="h-28 rounded-card" />
      <Skeleton className="h-12 rounded-full" />
      <Skeleton className="h-24 rounded-card" />
    </>
  );
}

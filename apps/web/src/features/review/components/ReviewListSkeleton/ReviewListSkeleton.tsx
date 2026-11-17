import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

/** Cards shaped like ReviewCard while the queue loads. */
export function ReviewListSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <div
      aria-busy="true"
      aria-label="Loading items to check"
      className="flex flex-col gap-4"
    >
      {Array.from({ length: cards }, (_, index) => (
        <div
          key={index}
          className="flex flex-col gap-4 rounded-card border border-border bg-card p-card"
        >
          <div className="flex flex-col gap-1">
            <p className="text-amount">
              <SkeletonText className="w-32" />
            </p>
            <p>
              <SkeletonText className="w-48" />
            </p>
          </div>
          <Skeleton className="h-12 rounded-inset" />
          <div className="grid grid-cols-2 gap-2">
            <Skeleton className="h-12 rounded-full" />
            <Skeleton className="h-12 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

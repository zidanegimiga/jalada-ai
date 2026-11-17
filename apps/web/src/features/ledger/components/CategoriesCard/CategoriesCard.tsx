import {
  CategoryBreakdown,
  type Slice,
} from "@/shared/components/CategoryBreakdown";
import { FolderCard } from "@/shared/components/FolderCard";
import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

/** Where money went and came from in a period, on a flax folder named for the period. */
export function CategoriesCard({
  tab,
  slices,
}: {
  tab: string;
  slices: { in: Slice[]; out: Slice[] };
}) {
  return (
    <FolderCard
      tab={tab}
      tone="flax"
      aria-labelledby="categories-heading"
      className="gap-4"
    >
      <h2 id="categories-heading" className="text-title">
        By category
      </h2>
      <CategoryBreakdown slices={slices} />
    </FolderCard>
  );
}

export function CategoriesCardSkeleton({ tab }: { tab: string }) {
  return (
    <FolderCard tab={tab} tone="flax" aria-busy="true" className="gap-4">
      <h2 className="text-title">By category</h2>
      <Skeleton className="h-tap w-56 rounded-full bg-current opacity-10" />
      <div className="flex flex-col gap-3.5">
        {[0, 1, 2].map((row) => (
          <div key={row} className="flex flex-col gap-1.5">
            <p>
              <SkeletonText className="w-40 bg-current opacity-15" />
            </p>
            <Skeleton className="h-2 rounded-full bg-current opacity-10" />
          </div>
        ))}
      </div>
    </FolderCard>
  );
}

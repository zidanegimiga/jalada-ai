import { FolderCard } from "@/shared/components/FolderCard";
import { InOutChart, type InOutPoint } from "@/shared/components/InOutChart";
import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

/** Money in and out over several months, on an ink folder whose tab names the period. */
export function MoneyChartCard({
  tab,
  points,
  current,
}: {
  tab: string;
  points: InOutPoint[];
  /** Which point is now, when later ones are still to come. */
  current?: number;
}) {
  return (
    <FolderCard tab={tab} aria-label={`Money in and out, ${tab.toLowerCase()}`}>
      <InOutChart points={points} current={current} />
    </FolderCard>
  );
}

/** The same card while the months load, at the same height. */
export function MoneyChartCardSkeleton({ tab }: { tab: string }) {
  return (
    <FolderCard tab={tab} aria-busy="true">
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end gap-x-5 gap-y-1">
          <p className="w-full text-small">
            <SkeletonText className="w-24 bg-current opacity-20" />
          </p>
          <p className="text-amount">
            <SkeletonText className="w-32 bg-current opacity-20" />
          </p>
          <p className="text-amount">
            <SkeletonText className="w-32 bg-current opacity-20" />
          </p>
        </div>
        <div className="flex flex-col gap-2 pb-1">
          <Skeleton className="h-32 bg-current opacity-10" />
          <p className="font-mono text-tiny">
            <SkeletonText className="w-full bg-current opacity-10" />
          </p>
        </div>
      </div>
    </FolderCard>
  );
}

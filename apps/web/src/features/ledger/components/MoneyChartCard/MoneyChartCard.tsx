import { BalanceLine } from "@/shared/components/BalanceLine";
import { ChartViews } from "@/shared/components/ChartViews";
import { FolderCard } from "@/shared/components/FolderCard";
import { InOutChart } from "@/shared/components/InOutChart";
import { PurposeColumns } from "@/shared/components/PurposeColumns";
import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";
import { YearWheel } from "@/shared/components/YearWheel";

import type { MonthPoint } from "../../charts";

/**
 * Money in and out over several months, on an ink folder whose tab names the period. The
 * same months can be seen as bars, as what was kept, split by business and personal, or
 * around a wheel.
 */
export function MoneyChartCard({
  tab,
  points,
  current = points.length - 1,
}: {
  tab: string;
  points: MonthPoint[];
  /** Which point is now, when later ones are still to come. */
  current?: number;
}) {
  const sofar = points.slice(0, current + 1);
  return (
    <FolderCard tab={tab} aria-label={`Money in and out, ${tab.toLowerCase()}`}>
      <ChartViews
        label="Show the months as"
        views={[
          {
            value: "bars",
            label: "Bars",
            content: <InOutChart points={points} current={current} />,
          },
          {
            value: "kept",
            label: "Kept",
            content: <BalanceLine points={points} current={current} />,
          },
          {
            value: "purpose",
            label: "Business",
            content: <PurposeColumns points={sofar} />,
          },
          {
            value: "wheel",
            label: "Wheel",
            content: <YearWheel points={sofar} />,
          },
        ]}
      />
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

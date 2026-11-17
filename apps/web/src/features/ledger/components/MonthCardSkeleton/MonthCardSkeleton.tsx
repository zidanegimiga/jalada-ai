import { SkeletonText } from "@/shared/components/Skeleton";

function Row({ label }: { label: string }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-small opacity-80">{label}</p>
      <p className="text-total">
        <SkeletonText className="w-40 bg-current opacity-20" />
      </p>
      <p className="text-small">
        <SkeletonText className="w-52 bg-current opacity-20" />
      </p>
    </div>
  );
}

/** MonthCard's shape while the month's totals load. */
export function MonthCardSkeleton() {
  return (
    <section
      aria-label="This month"
      aria-busy="true"
      className="flex flex-col gap-5 rounded-card bg-foreground p-card text-background dark:border dark:border-border dark:bg-card dark:text-card-foreground"
    >
      <h2 className="text-lead font-medium">
        <SkeletonText className="w-32 bg-current opacity-20" />
      </h2>
      <Row label="Money in" />
      <Row label="Money out" />
    </section>
  );
}

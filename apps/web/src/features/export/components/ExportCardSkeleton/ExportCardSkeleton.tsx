import { Label } from "@/shared/components/Label";
import { Skeleton } from "@/shared/components/Skeleton";

/** ExportCard's shape while the years load: the same words, with the controls held back. */
export function ExportCardSkeleton() {
  return (
    <section
      aria-labelledby="export-heading"
      aria-busy="true"
      className="flex flex-col gap-3 rounded-card border border-border bg-card p-card"
    >
      <h2 id="export-heading" className="text-title">
        For your tax return
      </h2>
      <p className="text-muted-foreground">
        Confirmed entries for one year, grouped the way iTax asks for them.
      </p>
      <Label>Year</Label>
      <Skeleton className="h-12" />
      <Skeleton className="h-14 rounded-full" />
    </section>
  );
}

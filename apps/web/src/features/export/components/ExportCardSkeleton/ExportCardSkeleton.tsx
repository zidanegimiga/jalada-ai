import { FolderCard } from "@/shared/components/FolderCard";
import { Label } from "@/shared/components/Label";
import { Skeleton } from "@/shared/components/Skeleton";

/** ExportCard's shape while the years load: the same words, with the controls held back. */
export function ExportCardSkeleton() {
  return (
    <FolderCard
      tab="Tax return"
      tone="flax"
      aria-labelledby="export-heading"
      aria-busy="true"
      className="gap-3"
    >
      <h2 id="export-heading" className="text-title">
        For your tax return
      </h2>
      <p className="opacity-75">
        Confirmed entries for one year, grouped the way iTax asks for them.
      </p>
      <Label>Year</Label>
      <Skeleton className="h-12" />
      <Skeleton className="h-14 rounded-full" />
    </FolderCard>
  );
}

import { cn } from "@/shared/styles/cn";

/**
 * A placeholder with the size of what is loading, so nothing moves when it arrives. Give it
 * the same height and shape classes as the real thing.
 */
export function Skeleton({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "block animate-pulse rounded-control bg-muted motion-reduce:animate-none",
        className,
      )}
    />
  );
}

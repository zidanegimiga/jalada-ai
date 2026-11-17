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

/**
 * A bar standing in for words inside a text element. The element's own line height sets the
 * height, so `<p className="text-total"><SkeletonText /></p>` is exactly as tall as a total.
 */
export function SkeletonText({ className }: { className?: string }) {
  return (
    <Skeleton
      className={cn(
        "inline-block h-[0.8em] w-24 rounded-full align-[-0.1em]",
        className,
      )}
    />
  );
}

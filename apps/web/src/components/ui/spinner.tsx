import { LoaderCircle } from "lucide-react";

import { cn } from "@/lib/utils";

type SpinnerProps = {
  /** What is loading, read out by screen readers. */
  label?: string;
  className?: string;
};

/** A spinning icon shown while content loads. Screen readers hear the label. */
export function Spinner({ label = "Loading", className }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex justify-center py-6 text-muted-foreground",
        className,
      )}
    >
      <LoaderCircle
        aria-hidden="true"
        className="size-8 motion-safe:animate-spin"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}

import { Check, LoaderCircle } from "lucide-react";

import type { Progress } from "../../types";

/** What the assistant is doing, in a few words, while the person waits. */
export function describe(progress: Progress): string {
  if (progress.stage === "looking_up") return progress.label ?? "Looking it up";
  if (progress.stage === "checking") return "Checking the figures";
  return "Thinking";
}

/**
 * Quiet lines under the conversation while a turn runs: each lookup made so far, then what
 * is happening now. Screen readers hear each change.
 */
export function ToolActivity({
  progress,
  lookups = [],
}: {
  progress: Progress | null;
  lookups?: string[];
}) {
  const now = progress && progress.stage !== "looking_up" ? progress : null;
  const looking = progress?.stage === "looking_up";
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex min-h-6 flex-col gap-1 text-small text-muted-foreground"
    >
      {progress && (
        <ul className="flex flex-col gap-1">
          {lookups.map((label, index) => {
            const running = looking && index === lookups.length - 1;
            const Icon = running ? LoaderCircle : Check;
            return (
              <li key={index} className="flex items-center gap-2">
                <Icon
                  aria-hidden="true"
                  className={
                    running ? "size-4 motion-safe:animate-spin" : "size-4"
                  }
                />
                {label}
              </li>
            );
          })}
          {now && (
            <li className="flex items-center gap-2">
              <LoaderCircle
                aria-hidden="true"
                className="size-4 motion-safe:animate-spin"
              />
              {describe(now)}...
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

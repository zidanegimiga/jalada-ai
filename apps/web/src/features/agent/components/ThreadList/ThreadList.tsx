import { History, Plus } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/shared/components/Button";
import { cn } from "@/shared/styles/cn";

import type { ThreadSummary } from "../../types";

const DAY = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  timeZone: "Africa/Nairobi",
});

/** Earlier conversations, folded away, and a way to start a new one. */
export function ThreadList({
  threads,
  current,
}: {
  threads: ThreadSummary[];
  current: string | null;
}) {
  return (
    <div className="flex flex-wrap items-start gap-2">
      {current && (
        <Link
          href="/ask"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          <Plus aria-hidden="true" />
          New conversation
        </Link>
      )}
      {threads.length > 0 && (
        <details className="group w-full rounded-card border border-border bg-card">
          <summary className="flex min-h-tap cursor-pointer list-none items-center gap-2 px-4 font-medium">
            <History aria-hidden="true" className="size-4" />
            Earlier conversations ({threads.length})
          </summary>
          <ul className="flex flex-col border-t border-border">
            {threads.map((thread) => (
              <li key={thread.id}>
                <Link
                  href={`/ask?thread=${thread.id}`}
                  aria-current={thread.id === current ? "page" : undefined}
                  className={cn(
                    "flex min-h-tap items-center justify-between gap-3 px-4 py-2 hover:bg-muted",
                    thread.id === current && "font-medium",
                  )}
                >
                  <span className="truncate">{thread.title}</span>
                  <span className="shrink-0 text-small text-muted-foreground">
                    {DAY.format(new Date(thread.updated_at))}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

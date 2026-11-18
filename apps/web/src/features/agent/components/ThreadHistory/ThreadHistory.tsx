"use client";

import { MessageCircle, Plus } from "lucide-react";
import Link from "next/link";
import type { CSSProperties } from "react";

import { cn } from "@/shared/styles/cn";

import type { ThreadSummary } from "../../types";

const DAY = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  timeZone: "Africa/Nairobi",
});

type ThreadHistoryProps = {
  threads: ThreadSummary[];
  current: string | null;
  /** Called when the person picks a conversation, so a drawer can close. */
  onPick?: () => void;
};

/**
 * Earlier conversations, latest first, with a way to start a new one. The current one is
 * marked; the rest fade in one after another.
 */
export function ThreadHistory({
  threads,
  current,
  onPick,
}: ThreadHistoryProps) {
  return (
    <nav aria-label="Conversations" className="flex flex-col gap-3">
      <Link
        href="/ask"
        onClick={onPick}
        aria-current={current === null ? "page" : undefined}
        className="group flex min-h-tap items-center gap-2 rounded-control border border-dashed border-border px-3 font-medium transition-colors hover:border-foreground/40 hover:bg-muted aria-[current=page]:border-solid aria-[current=page]:bg-muted"
      >
        <Plus
          aria-hidden="true"
          className="size-4 transition-transform duration-300 group-hover:rotate-90"
        />
        New conversation
      </Link>
      {threads.length === 0 ? (
        <p className="px-1 text-small text-muted-foreground">
          Your conversations will be listed here.
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {threads.map((thread, index) => {
            const here = thread.id === current;
            return (
              <li
                key={thread.id}
                className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-right-2 motion-safe:fill-mode-both motion-safe:duration-300"
                style={
                  {
                    animationDelay: `${Math.min(index, 10) * 30}ms`,
                  } as CSSProperties
                }
              >
                <Link
                  href={`/ask?thread=${thread.id}`}
                  onClick={onPick}
                  aria-current={here ? "page" : undefined}
                  className={cn(
                    "relative flex min-h-tap items-center gap-3 rounded-control py-2 pr-3 pl-4 transition-colors hover:bg-muted",
                    here && "bg-muted font-medium",
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-y-2 left-0 w-1 rounded-full bg-primary transition-[opacity,scale] duration-300",
                      here ? "opacity-100" : "scale-y-0 opacity-0",
                    )}
                  />
                  <MessageCircle
                    aria-hidden="true"
                    className="size-4 shrink-0 text-muted-foreground"
                  />
                  <span className="min-w-0 flex-1 truncate">
                    {thread.title}
                  </span>
                  <span className="shrink-0 text-small text-muted-foreground">
                    {DAY.format(new Date(thread.updated_at))}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </nav>
  );
}

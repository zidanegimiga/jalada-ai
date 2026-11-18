"use client";

import { History, Plus } from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";

import { buttonVariants } from "@/shared/components/Button";
import { Drawer } from "@/shared/components/Drawer";
import { cn } from "@/shared/styles/cn";

import type { ThreadSummary } from "../../types";
import { ThreadAnswered, useThreadList } from "../../hooks/useThreadList";
import { ThreadHistory } from "../ThreadHistory";

type AskLayoutProps = {
  threads: ThreadSummary[];
  current: string | null;
  /** The conversation itself, with its input pinned to the bottom. */
  children: ReactNode;
};

/**
 * The Ask page: the conversation fills the space with its input at the bottom, and earlier
 * conversations sit in a rail on the right. On a phone the rail becomes a drawer, opened from
 * the History button beside the title.
 */
export function AskLayout(props: AskLayoutProps) {
  const { children } = props;
  const { threads, current, answered } = useThreadList(
    props.threads,
    props.current,
  );
  const [open, setOpen] = useState(false);
  return (
    <ThreadAnswered value={answered}>
      <div className="flex min-h-[calc(100dvh-13.5rem-env(safe-area-inset-top))] flex-1 flex-col gap-6 lg:min-h-[calc(100dvh-6.5rem)]">
        <div className="flex items-center gap-2">
          <h1 className="mr-auto text-display">Ask</h1>
          {current && (
            <Link
              href="/ask"
              aria-label="New conversation"
              className={cn(
                buttonVariants({ variant: "outline", size: "icon-sm" }),
                "lg:hidden",
              )}
            >
              <Plus aria-hidden="true" />
            </Link>
          )}
          <Drawer
            title="Conversations"
            open={open}
            onOpenChange={setOpen}
            trigger={
              <button
                type="button"
                className={cn(
                  buttonVariants({ variant: "outline", size: "sm" }),
                  "lg:hidden",
                )}
              >
                <History aria-hidden="true" />
                History
              </button>
            }
          >
            <ThreadHistory
              threads={threads}
              current={current}
              onPick={() => setOpen(false)}
            />
          </Drawer>
        </div>
        <div className="flex flex-1 flex-col gap-8 lg:grid lg:grid-cols-[minmax(0,1fr)_17rem] lg:items-stretch">
          <div className="flex min-w-0 flex-1 flex-col">{children}</div>
          <aside aria-label="Earlier conversations" className="hidden lg:block">
            <div className="sticky top-10 max-h-[calc(100dvh-5rem)] overflow-y-auto border-l border-border pl-6 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-right-4 motion-safe:duration-500">
              <ThreadHistory threads={threads} current={current} />
            </div>
          </aside>
        </div>
      </div>
    </ThreadAnswered>
  );
}

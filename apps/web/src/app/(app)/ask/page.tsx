import { MessageCircle } from "lucide-react";
import { Suspense } from "react";

import { AskLayout } from "@/features/agent/components/AskLayout";
import { ChatPanel } from "@/features/agent/components/ChatPanel";
import { getThread, getThreads } from "@/features/agent/server/queries";
import { EmptyState } from "@/shared/components/EmptyState";
import { Skeleton } from "@/shared/components/Skeleton";

type AskSearch = Promise<{ thread?: string }>;

async function Conversation({ search }: { search: AskSearch }) {
  const { thread: threadId } = await search;
  const [threads, thread] = await Promise.all([
    getThreads(),
    threadId ? getThread(threadId) : null,
  ]);
  if (threads === null) {
    return (
      <div className="mx-auto flex w-full max-w-content flex-col gap-section">
        <h1 className="text-display">Ask</h1>
        <EmptyState Icon={MessageCircle} title="Not available yet">
          <p>Asking about your records is not switched on here yet.</p>
        </EmptyState>
      </div>
    );
  }
  return (
    <AskLayout threads={threads} current={thread?.id ?? null}>
      {/* A new key starts a fresh conversation when the address changes. */}
      <ChatPanel key={thread?.id ?? "new"} initial={thread} />
    </AskLayout>
  );
}

function ConversationSkeleton() {
  return (
    <div
      aria-busy="true"
      className="flex min-h-[calc(100dvh-13.5rem)] flex-col gap-6 lg:min-h-[calc(100dvh-6.5rem)]"
    >
      <h1 className="text-display">Ask</h1>
      <div className="flex flex-1 flex-col gap-8 lg:grid lg:grid-cols-[minmax(0,1fr)_17rem]">
        <div className="flex flex-1 flex-col justify-end gap-3">
          <Skeleton className="ml-auto h-12 w-2/3 rounded-card" />
          <Skeleton className="h-20 w-3/4 rounded-card" />
          <Skeleton className="h-16 w-full rounded-card" />
        </div>
        <div className="hidden flex-col gap-2 border-l border-border pl-6 lg:flex">
          <Skeleton className="h-tap w-full rounded-control" />
          <Skeleton className="h-tap w-full rounded-control" />
          <Skeleton className="h-tap w-full rounded-control" />
        </div>
      </div>
    </div>
  );
}

export default function AskPage({ searchParams }: { searchParams: AskSearch }) {
  return (
    <Suspense fallback={<ConversationSkeleton />}>
      <Conversation search={searchParams} />
    </Suspense>
  );
}

import { MessageCircle } from "lucide-react";
import { Suspense } from "react";

import { ChatPanel } from "@/features/agent/components/ChatPanel";
import { ThreadList } from "@/features/agent/components/ThreadList";
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
      <EmptyState Icon={MessageCircle} title="Not available yet">
        <p>Asking about your records is not switched on here yet.</p>
      </EmptyState>
    );
  }
  return (
    <>
      <ThreadList threads={threads} current={thread?.id ?? null} />
      {/* A new key starts a fresh conversation when the address changes. */}
      <ChatPanel key={thread?.id ?? "new"} initial={thread} />
    </>
  );
}

function ConversationSkeleton() {
  return (
    <div aria-busy="true" className="flex flex-col gap-4">
      <Skeleton className="h-tap w-full rounded-card" />
      <Skeleton className="h-24 w-full rounded-card" />
      <Skeleton className="h-16 w-full rounded-card" />
    </div>
  );
}

export default function AskPage({ searchParams }: { searchParams: AskSearch }) {
  return (
    <div className="mx-auto flex w-full max-w-content flex-1 flex-col gap-section">
      <h1 className="text-display">Ask</h1>
      <Suspense fallback={<ConversationSkeleton />}>
        <Conversation search={searchParams} />
      </Suspense>
    </div>
  );
}

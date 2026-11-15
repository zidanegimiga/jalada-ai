import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { Spinner } from "@/components/ui/spinner";
import { HowPaidCard } from "@/features/review/components/how-paid-card";
import { MatchCard } from "@/features/review/components/match-card";
import { ReviewCard } from "@/features/review/components/review-card";
import {
  getCategories,
  getReviewQueue,
} from "@/features/review/server/queries";

async function ReviewQueue() {
  const [items, categories] = await Promise.all([
    getReviewQueue(),
    getCategories(),
  ]);
  if (items.length === 0) {
    return (
      <p className="text-lg text-muted-foreground">
        All caught up. Nothing is waiting for you.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      {items.map((item) =>
        item.match ? (
          <MatchCard key={item.match.suggestion_id} item={item} />
        ) : item.ask_how_paid ? (
          <HowPaidCard key={item.evidence.id} item={item} />
        ) : (
          <ReviewCard
            key={item.entry?.id ?? item.evidence.id}
            item={item}
            categories={categories}
          />
        ),
      )}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <AppShell>
      <h1 className="text-4xl font-bold">To check</h1>
      <Suspense fallback={<Spinner />}>
        <ReviewQueue />
      </Suspense>
    </AppShell>
  );
}

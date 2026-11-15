import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { Spinner } from "@/components/ui/spinner";
import { ReviewList } from "@/features/review/components/review-list";
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
  return <ReviewList items={items} categories={categories} />;
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

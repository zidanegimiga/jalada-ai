import Link from "next/link";
import { Suspense } from "react";

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
      {items.map((item) => (
        <ReviewCard
          key={item.entry?.id ?? item.evidence.id}
          item={item}
          categories={categories}
        />
      ))}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 py-8">
      <Link href="/" className="text-lg font-bold">
        Jalada AI
      </Link>
      <h1 className="text-4xl font-bold">To check</h1>
      <Suspense fallback={<p className="text-muted-foreground">Loading...</p>}>
        <ReviewQueue />
      </Suspense>
    </main>
  );
}

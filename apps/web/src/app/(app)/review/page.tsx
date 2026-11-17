import { CheckCheck } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { AppShell } from "@/app/(app)/_components/AppShell";
import { buttonVariants } from "@/shared/components/Button";
import { EmptyState } from "@/shared/components/EmptyState";
import { Spinner } from "@/shared/components/Spinner";
import { ReviewList } from "@/features/review/components/ReviewList";
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
      <EmptyState
        Icon={CheckCheck}
        title="All caught up"
        action={
          <Link href="/" className={buttonVariants({ variant: "outline" })}>
            Add a message or receipt
          </Link>
        }
      >
        <p>
          When Jalada AI reads something and is not sure of it, it waits here
          for you to confirm or change.
        </p>
      </EmptyState>
    );
  }
  return <ReviewList items={items} categories={categories} />;
}

export default function ReviewPage() {
  return (
    <AppShell>
      <h1 className="text-display">To check</h1>
      <Suspense fallback={<Spinner />}>
        <ReviewQueue />
      </Suspense>
    </AppShell>
  );
}

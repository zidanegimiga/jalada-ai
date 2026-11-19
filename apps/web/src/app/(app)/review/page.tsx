import { CheckCheck } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { buttonVariants } from "@/shared/components/Button";
import { EmptyState } from "@/shared/components/EmptyState";
import { ReviewList } from "@/features/review/components/ReviewList";
import { ReviewListSkeleton } from "@/features/review/components/ReviewListSkeleton";
import {
  getCategories,
  getReviewQueue,
} from "@/features/review/server/queries";
import { PageHeader } from "@/app/(app)/_components/PageHeader";

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
    <div className="mx-auto flex w-full max-w-content flex-col gap-section">
      <PageHeader title="To check" back={{ href: "/", label: "Home" }} />
      <Suspense fallback={<ReviewListSkeleton />}>
        <ReviewQueue />
      </Suspense>
    </div>
  );
}

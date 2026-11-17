import type { Category, ReviewItem } from "../../types";
import { ConfirmAll } from "../ConfirmAll";
import { HowPaidCard } from "../HowPaidCard";
import { MatchCard } from "../MatchCard";
import { ReviewCard } from "../ReviewCard";

function Card({
  item,
  categories,
}: {
  item: ReviewItem;
  categories: Category[];
}) {
  if (item.match) return <MatchCard item={item} />;
  if (item.ask_how_paid) return <HowPaidCard item={item} />;
  return <ReviewCard item={item} categories={categories} />;
}

function key(item: ReviewItem): string {
  return item.match?.suggestion_id ?? item.entry?.id ?? item.evidence.id;
}

/** Questions first, then the payments ready to confirm, with Confirm all when there
 * are two or more. */
export function ReviewList({
  items,
  categories,
}: {
  items: ReviewItem[];
  categories: Category[];
}) {
  const questions = items.filter((item) => !item.ready);
  const ready = items.filter((item) => item.ready);
  const entries = ready.flatMap((item) => (item.entry ? [item.entry] : []));
  return (
    <div className="flex flex-col gap-4">
      {questions.map((item) => (
        <Card key={key(item)} item={item} categories={categories} />
      ))}
      {ready.length > 0 && (
        <section className="flex flex-col gap-4" aria-labelledby="ready">
          <h2 id="ready" className="text-title">
            Ready to confirm
          </h2>
          {entries.length > 1 && <ConfirmAll entries={entries} />}
          {ready.map((item) => (
            <Card key={key(item)} item={item} categories={categories} />
          ))}
        </section>
      )}
    </div>
  );
}

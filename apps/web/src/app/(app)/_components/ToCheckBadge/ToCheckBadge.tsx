import { getReviewQueue } from "@/features/review/server/queries";

/** How many items wait on To check. Nothing at all when none do. */
export async function ToCheckBadge() {
  const count = (await getReviewQueue()).length;
  if (count === 0) return null;
  const shown = count > 99 ? "99+" : String(count);
  return (
    <>
      <span
        aria-hidden="true"
        className="flex h-5 min-w-5 items-center justify-center rounded-full bg-(--flax) px-1 text-tiny font-bold text-(--black) ring-2 ring-(--badge-ring,transparent) motion-safe:animate-in motion-safe:zoom-in-50 motion-safe:duration-300"
      >
        {shown}
      </span>
      <span className="sr-only">, {count} waiting</span>
    </>
  );
}

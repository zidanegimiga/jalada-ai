import type { CSSProperties } from "react";

import { formatKsh } from "@/shared/format/format";

type Slice = { name: string; cents: number };

/** Colours for the categories in order, drawn for a flax card in either theme. */
const TONES = [
  "var(--pumpkin)",
  "currentColor",
  "var(--money-in)",
  "var(--emphasis)",
  "color-mix(in oklab, currentColor 45%, transparent)",
  "color-mix(in oklab, currentColor 18%, transparent)",
];

/**
 * Shares of 100 squares, by the largest remainder, so the squares always add up to 100.
 */
export function squares(slices: Slice[]): number[] {
  const total = slices.reduce((sum, slice) => sum + slice.cents, 0);
  if (total <= 0) return slices.map(() => 0);
  const exact = slices.map((slice) => (slice.cents / total) * 100);
  const whole = exact.map(Math.floor);
  const left = 100 - whole.reduce((sum, count) => sum + count, 0);
  const bumped = new Set(
    exact
      .map((value, index) => ({ index, rest: value - whole[index] }))
      .sort((a, b) => b.rest - a.rest)
      .slice(0, left)
      .map(({ index }) => index),
  );
  return whole.map((count, index) => count + (bumped.has(index) ? 1 : 0));
}

function Grid({ title, slices }: { title: string; slices: Slice[] }) {
  const counts = squares(slices);
  const cells = counts.flatMap((count, index) =>
    Array<number>(count).fill(index),
  );
  return (
    <figure className="flex flex-col gap-3">
      <figcaption className="font-medium">{title}</figcaption>
      {slices.length === 0 ? (
        <p className="opacity-75">Nothing confirmed yet.</p>
      ) : (
        <>
          <div
            role="img"
            aria-label={slices
              .map((slice, index) => `${slice.name} ${counts[index]}%`)
              .join(", ")}
            className="grid w-full max-w-60 grid-cols-10 gap-1"
          >
            {cells.map((tone, index) => (
              <span
                key={index}
                className="waffle-cell aspect-square rounded-[3px]"
                style={
                  {
                    background: TONES[tone % TONES.length],
                    "--cell": index,
                  } as CSSProperties
                }
              />
            ))}
          </div>
          <ul className="flex flex-col gap-1.5 text-small">
            {slices.map((slice, index) => (
              <li key={slice.name} className="flex items-center gap-2">
                <span
                  className="size-3 shrink-0 rounded-[3px]"
                  style={{ background: TONES[index % TONES.length] }}
                />
                <span className="truncate">{slice.name}</span>
                <span className="ml-auto shrink-0 tabular-nums opacity-75">
                  {formatKsh(slice.cents)}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </figure>
  );
}

/** Where money went and came from, each as 100 squares, one square a percent. */
export function CategoryWaffle({
  slices,
}: {
  slices: { in: Slice[]; out: Slice[] };
}) {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <Grid title="Money out" slices={slices.out} />
      <Grid title="Money in" slices={slices.in} />
    </div>
  );
}

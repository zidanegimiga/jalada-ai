import { formatKsh } from "@/shared/format/format";

type Slice = { name: string; cents: number };
type Placed = Slice & { top: number; height: number };

/** The drawing's own units: 100 a side, and this tall. */
const HEIGHT = 240;
const GAP = 10;

/** Stacks the slices from `start`, each as tall as its amount, `gap` apart. */
function stack(slices: Slice[], scale: number, start = 0, gap = GAP) {
  return slices.reduce<Placed[]>((placed, slice) => {
    const last = placed.at(-1);
    const top = last ? last.top + last.height + gap : start;
    const height = Math.max(2, slice.cents * scale);
    return [...placed, { ...slice, top, height }];
  }, []);
}

/** A band from one side to the middle, as tall at both ends. */
function ribbon(fromX: number, from: Placed, toX: number, toTop: number) {
  const mid = (fromX + toX) / 2;
  const bottom = from.top + from.height;
  const toBottom = toTop + from.height;
  return [
    `M${fromX} ${from.top} C${mid} ${from.top} ${mid} ${toTop} ${toX} ${toTop}`,
    `L${toX} ${toBottom} C${mid} ${toBottom} ${mid} ${bottom} ${fromX} ${bottom} Z`,
  ].join(" ");
}

function describe(slices: { in: Slice[]; out: Slice[] }): string {
  const list = (side: Slice[]) =>
    side.map((s) => `${s.name} ${formatKsh(s.cents)}`).join(", ");
  return `Money in: ${list(slices.in)}. Money out: ${list(slices.out)}.`;
}

/** The names down one side, each level with the middle of its band. */
function Labels({ placed, side }: { placed: Placed[]; side: "in" | "out" }) {
  return (
    <ul aria-hidden="true" className="relative h-56">
      {placed.map((slice) => (
        <li
          key={slice.name}
          className={`absolute inset-x-0 -translate-y-1/2 truncate text-tiny ${side === "in" ? "text-right" : ""}`}
          style={{ top: `${((slice.top + slice.height / 2) / HEIGHT) * 100}%` }}
        >
          {slice.name}
        </li>
      ))}
    </ul>
  );
}

/**
 * Where money came from, through you, to where it went: money in by category on the left,
 * money out on the right, each band as wide as its amount. Drawn for a flax card.
 */
export function MoneyFlow({
  slices,
}: {
  slices: { in: Slice[]; out: Slice[] };
}) {
  const totalIn = slices.in.reduce((sum, s) => sum + s.cents, 0);
  const totalOut = slices.out.reduce((sum, s) => sum + s.cents, 0);
  if (totalIn + totalOut === 0) {
    return <p className="opacity-75">Nothing confirmed yet to draw.</p>;
  }
  const gaps = (Math.max(slices.in.length, slices.out.length) - 1) * GAP;
  const scale = (HEIGHT - gaps) / Math.max(totalIn, totalOut);
  const left = stack(slices.in, scale);
  const right = stack(slices.out, scale);
  // Where each band meets the middle: packed together and centred, with no gaps.
  const intoMiddle = stack(slices.in, scale, (HEIGHT - totalIn * scale) / 2, 0);
  const outOfMiddle = stack(slices.out, scale, (HEIGHT - totalOut * scale) / 2, 0);
  const trunk = Math.max(totalIn, totalOut) * scale;

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_minmax(6rem,2fr)_minmax(0,1fr)] gap-2">
      <Labels placed={left} side="in" />
      <svg
        viewBox={`0 0 200 ${HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={describe(slices)}
        className="h-56 w-full overflow-visible"
      >
        {left.map((slice, index) => (
          <path
            key={`in-${slice.name}`}
            d={ribbon(0, slice, 100, intoMiddle[index].top)}
            fill="var(--money-in)"
            fillOpacity="0.4"
            className="flow-band"
          />
        ))}
        {right.map((slice, index) => (
          <path
            key={`out-${slice.name}`}
            d={ribbon(100, outOfMiddle[index], 200, slice.top)}
            fill="var(--pumpkin)"
            fillOpacity="0.5"
            className="flow-band"
          />
        ))}
        <rect
          x="98"
          y={(HEIGHT - trunk) / 2}
          width="4"
          height={trunk}
          fill="currentColor"
        />
      </svg>
      <Labels placed={right} side="out" />
    </div>
  );
}

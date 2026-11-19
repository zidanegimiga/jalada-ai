import { Amount } from "@/shared/components/Amount";
import { formatKsh } from "@/shared/format/format";

type Point = { key: string; short: string; inCents: number; outCents: number };

const WIDTH = 360;
const HEIGHT = 140;
const PAD = 12;

/** What is left after money out, added up month by month: where the year stands so far. */
export function runningNet(points: Point[], current: number): number[] {
  return points.slice(0, current + 1).reduce<number[]>((totals, point) => {
    const before = totals.at(-1) ?? 0;
    return [...totals, before + point.inCents - point.outCents];
  }, []);
}

/**
 * The year as one line: money kept, added up month by month. Above the dashed line the
 * months so far brought in more than went out; below, less. Drawn for an ink card.
 */
export function BalanceLine({
  points,
  current = points.length - 1,
}: {
  points: Point[];
  current?: number;
}) {
  const totals = runningNet(points, current);
  const high = Math.max(0, ...totals);
  const low = Math.min(0, ...totals);
  const span = high - low || 1;
  const x = (index: number) =>
    PAD + (index * (WIDTH - PAD * 2)) / Math.max(1, points.length - 1);
  const y = (cents: number) =>
    PAD + ((high - cents) * (HEIGHT - PAD * 2)) / span;
  const line = totals
    .map((cents, index) => `${index ? "L" : "M"}${x(index)} ${y(cents)}`)
    .join(" ");
  const area = `${line} L${x(totals.length - 1)} ${y(0)} L${x(0)} ${y(0)} Z`;
  const last = totals.at(-1) ?? 0;

  return (
    <div className="flex flex-col gap-4">
      <p className="flex flex-wrap items-baseline gap-x-3">
        <span className="text-small opacity-70">Kept so far</span>
        <Amount cents={last} fadeCents className="text-amount" />
      </p>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT + 22}`}
        role="img"
        aria-label={`Money kept, month by month: ${totals
          .map((cents, index) => `${points[index].short} ${formatKsh(cents)}`)
          .join(", ")}`}
        className="w-full overflow-visible"
      >
        <line
          x1={PAD}
          x2={WIDTH - PAD}
          y1={y(0)}
          y2={y(0)}
          stroke="currentColor"
          strokeOpacity="0.35"
          strokeDasharray="3 5"
        />
        <path d={area} fill="var(--flax)" fillOpacity="0.14" />
        <path
          d={line}
          fill="none"
          stroke="var(--flax)"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
          className="balance-line"
          pathLength={1}
        />
        {totals.map((cents, index) => (
          <circle
            key={points[index].key}
            cx={x(index)}
            cy={y(cents)}
            r={index === totals.length - 1 ? 5 : 3}
            fill={cents < 0 ? "var(--pumpkin)" : "var(--flax)"}
          />
        ))}
        {points.map((point, index) => (
          <text
            key={point.key}
            x={x(index)}
            y={HEIGHT + 18}
            textAnchor="middle"
            className="fill-current font-mono text-[9px]"
            opacity={index <= current ? 0.7 : 0.3}
          >
            {point.short[0]}
          </text>
        ))}
      </svg>
    </div>
  );
}

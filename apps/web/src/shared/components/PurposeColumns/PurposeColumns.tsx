import type { CSSProperties } from "react";

import { formatKsh } from "@/shared/format/format";

type Point = {
  key: string;
  short: string;
  label: string;
  inCents: number;
  outCents: number;
  inBusinessCents: number;
  outBusinessCents: number;
};

const WIDTH = 360;
const HALF = 70;
const GAP = 4;

const KEY = [
  { label: "In, business", tone: "bg-(--flax)" },
  { label: "In, personal", tone: "bg-(--flax)/40" },
  { label: "Out, business", tone: "bg-(--pumpkin)" },
  { label: "Out, personal", tone: "bg-(--pumpkin)/40" },
];

function describe(p: Point): string {
  return `${p.label}: in ${formatKsh(p.inCents)}, ${formatKsh(p.inBusinessCents)} of it business; out ${formatKsh(p.outCents)}, ${formatKsh(p.outBusinessCents)} of it business`;
}

/**
 * Each month as a column standing on a middle line: money in rises above it, money out
 * hangs below. Each part is split into business (solid) and personal (pale), so a month
 * where the household ate into the business shows at a glance. Drawn for an ink card.
 */
export function PurposeColumns({ points }: { points: Point[] }) {
  const largest = Math.max(
    1,
    ...points.flatMap((p) => [p.inCents, p.outCents]),
  );
  const step = (WIDTH - 8) / Math.max(1, points.length);
  const bar = Math.min(18, step * 0.6);
  const size = (cents: number) => (cents / largest) * (HALF - GAP);
  const middle = HALF + 4;

  return (
    <div className="flex flex-col gap-4">
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-small">
        {KEY.map((item) => (
          <li key={item.label} className="flex items-center gap-2">
            <span className={`size-2.5 rounded-full ${item.tone}`} />
            {item.label}
          </li>
        ))}
      </ul>
      <svg
        viewBox={`0 0 ${WIDTH} ${middle * 2 + 16}`}
        role="img"
        aria-label={points.map(describe).join(". ")}
        className="w-full"
      >
        {points.map((p, index) => {
          const x = 4 + index * step + (step - bar) / 2;
          const rects = [
            {
              y: middle - GAP / 2 - size(p.inCents),
              h: size(p.inCents),
              fill: "var(--flax)",
              pale: true,
            },
            {
              y: middle - GAP / 2 - size(p.inBusinessCents),
              h: size(p.inBusinessCents),
              fill: "var(--flax)",
              pale: false,
            },
            {
              y: middle + GAP / 2,
              h: size(p.outCents),
              fill: "var(--pumpkin)",
              pale: true,
            },
            {
              y: middle + GAP / 2,
              h: size(p.outBusinessCents),
              fill: "var(--pumpkin)",
              pale: false,
            },
          ];
          return (
            <g
              key={p.key}
              className="purpose-column"
              style={{ "--column": index } as CSSProperties}
            >
              {rects.map((rect, part) => (
                <rect
                  key={part}
                  x={x}
                  y={rect.y}
                  width={bar}
                  height={rect.h}
                  rx={3}
                  fill={rect.fill}
                  fillOpacity={rect.pale ? 0.4 : 1}
                />
              ))}
              <text
                x={x + bar / 2}
                y={middle * 2 + 12}
                textAnchor="middle"
                className="fill-current font-mono text-[9px]"
                opacity="0.7"
              >
                {p.short[0]}
              </text>
            </g>
          );
        })}
        <line
          x1="0"
          x2={WIDTH}
          y1={middle}
          y2={middle}
          stroke="currentColor"
          strokeOpacity="0.3"
        />
      </svg>
    </div>
  );
}

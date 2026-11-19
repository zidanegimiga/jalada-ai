import type { CSSProperties } from "react";

import { Amount } from "@/shared/components/Amount";
import { formatKsh } from "@/shared/format/format";

type Point = {
  key: string;
  short: string;
  label: string;
  inCents: number;
  outCents: number;
};

const SIZE = 290;
const CENTRE = SIZE / 2;
const INNER = 62;
const REACH = 58;

function spoke(angle: number, from: number, to: number) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return {
    x1: CENTRE + cos * from,
    y1: CENTRE + sin * from,
    x2: CENTRE + cos * to,
    y2: CENTRE + sin * to,
  };
}

/**
 * The months around a clock face, the first at the top. Each month has two spokes: money in
 * (flax) and money out (pumpkin), longer for more. What was kept sits in the middle.
 * Drawn for an ink card.
 */
export function YearWheel({ points }: { points: Point[] }) {
  const largest = Math.max(
    1,
    ...points.flatMap((p) => [p.inCents, p.outCents]),
  );
  const length = (cents: number) =>
    cents > 0 ? 4 + (cents / largest) * REACH : 0;
  const turn = (Math.PI * 2) / Math.max(1, points.length);
  const kept = points.reduce((sum, p) => sum + p.inCents - p.outCents, 0);

  return (
    <div className="relative mx-auto w-full max-w-[18rem]">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={points
          .map(
            (p) =>
              `${p.label}: in ${formatKsh(p.inCents)}, out ${formatKsh(p.outCents)}`,
          )
          .join(". ")}
        className="w-full"
      >
        <circle
          cx={CENTRE}
          cy={CENTRE}
          r={INNER + REACH + 4}
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.12"
          strokeDasharray="2 6"
        />
        {points.map((p, index) => {
          const angle = index * turn - Math.PI / 2;
          const label = spoke(angle, 0, INNER + REACH + 16);
          return (
            <g
              key={p.key}
              className="wheel-month"
              style={{ "--month": index } as CSSProperties}
            >
              <line
                {...spoke(
                  angle - turn * 0.16,
                  INNER,
                  INNER + length(p.inCents),
                )}
                stroke="var(--flax)"
                strokeWidth="7"
                strokeLinecap="round"
              />
              <line
                {...spoke(
                  angle + turn * 0.16,
                  INNER,
                  INNER + length(p.outCents),
                )}
                stroke="var(--pumpkin)"
                strokeWidth="7"
                strokeLinecap="round"
              />
              <text
                x={label.x2}
                y={label.y2}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-current font-mono text-[10px]"
                opacity="0.7"
              >
                {p.short.slice(0, 3)}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="absolute inset-0 m-auto flex size-fit flex-col items-center text-center">
        <span className="font-mono text-tiny opacity-70">Kept</span>
        <Amount cents={kept} className="text-small font-bold" />
      </p>
    </div>
  );
}

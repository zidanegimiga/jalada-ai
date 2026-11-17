"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";

import { Amount } from "@/shared/components/Amount";
import { formatKsh } from "@/shared/format/format";
import { cn } from "@/shared/styles/cn";

import "./InOutChart.css";

export type InOutPoint = {
  key: string;
  label: string;
  short: string;
  inCents: number;
  outCents: number;
};

const HEIGHT = 120;
const COLUMN = 40;
const BAR = 11;

/** A bar's height: zero stays flat, anything else shows at least a sliver. */
function barHeight(cents: number, largest: number): number {
  if (cents <= 0 || largest <= 0) return 0;
  return Math.max(3, (cents / largest) * HEIGHT);
}

/**
 * Money in (flax) beside money out (pumpkin) for each month, drawn for an ink card. Each
 * month is a button: choosing one shows its amounts above the chart, which is also how
 * screen readers read it.
 */
export function InOutChart({
  points,
  current = points.length - 1,
}: {
  points: InOutPoint[];
  /** The month that is now. Later months have no bars and cannot be chosen. */
  current?: number;
}) {
  const [chosen, setChosen] = useState(current);
  const scroller = useRef<HTMLDivElement>(null);

  // Show this month without scrolling when a year is wider than the screen.
  useEffect(() => {
    const box = scroller.current;
    if (!box) return;
    box.scrollLeft =
      (box.scrollWidth * (current + 1)) / points.length - box.clientWidth;
  }, [current, points.length]);
  const largest = Math.max(
    1,
    ...points.flatMap((p) => [p.inCents, p.outCents]),
  );
  const shown = points[chosen];
  const width = points.length * COLUMN;

  return (
    <div className="flex flex-col gap-4">
      <div
        aria-live="polite"
        className="flex flex-wrap items-end gap-x-5 gap-y-1"
      >
        <p className="w-full text-small opacity-70">{shown.label}</p>
        <p className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="size-2.5 rounded-full bg-(--flax)"
          />
          <span className="text-small opacity-70">In</span>
          <Amount cents={shown.inCents} fadeCents className="text-amount" />
        </p>
        <p className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="size-2.5 rounded-full bg-(--pumpkin)"
          />
          <span className="text-small opacity-70">Out</span>
          <Amount cents={shown.outCents} fadeCents className="text-amount" />
        </p>
      </div>
      {/* Each month stays at least a thumb wide; a year scrolls sideways on a phone. */}
      <div ref={scroller} className="-mx-1 overflow-x-auto px-1 pb-1">
        <div
          style={{ minWidth: points.length * 44 }}
          className="flex flex-col gap-2"
        >
          <div className="relative">
            <svg
              aria-hidden="true"
              viewBox={`0 0 ${width} ${HEIGHT + 2}`}
              preserveAspectRatio="none"
              className="block h-32 w-full"
            >
              {points.map((p, column) => {
                const x = column * COLUMN + (COLUMN - BAR * 2 - 3) / 2;
                const later = column > current;
                const inH = later ? 0 : barHeight(p.inCents, largest);
                const outH = later ? 0 : barHeight(p.outCents, largest);
                const style = { "--column": column } as CSSProperties;
                return (
                  <g key={p.key} opacity={column === chosen ? 1 : 0.55}>
                    <rect
                      className="in-out-bar"
                      style={style}
                      x={x}
                      y={HEIGHT - inH}
                      width={BAR}
                      height={inH}
                      rx={3}
                      fill="var(--flax)"
                    />
                    <rect
                      className="in-out-bar"
                      style={style}
                      x={x + BAR + 3}
                      y={HEIGHT - outH}
                      width={BAR}
                      height={outH}
                      rx={3}
                      fill="var(--pumpkin)"
                    />
                  </g>
                );
              })}
              <line
                x1={0}
                x2={width}
                y1={HEIGHT + 1}
                y2={HEIGHT + 1}
                stroke="currentColor"
                strokeOpacity={0.3}
                strokeDasharray="3 4"
              />
            </svg>
            <div
              className="absolute inset-0 grid"
              style={{
                gridTemplateColumns: `repeat(${points.length}, minmax(0, 1fr))`,
              }}
            >
              {points.map((p, column) => (
                <button
                  key={p.key}
                  type="button"
                  aria-pressed={column === chosen}
                  disabled={column > current}
                  aria-label={`${p.label}: in ${formatKsh(p.inCents)}, out ${formatKsh(p.outCents)}`}
                  onClick={() => setChosen(column)}
                  className={cn(
                    "rounded-control transition-colors disabled:cursor-default",
                    column === chosen
                      ? "bg-white/[0.06]"
                      : "hover:bg-white/[0.04]",
                  )}
                />
              ))}
            </div>
          </div>
          <div
            aria-hidden="true"
            className="grid font-mono text-tiny opacity-60"
            style={{
              gridTemplateColumns: `repeat(${points.length}, minmax(0, 1fr))`,
            }}
          >
            {points.map((p, column) => (
              <span
                key={p.key}
                className={cn(
                  "text-center",
                  column === chosen && "font-bold opacity-100",
                  column > current && "opacity-40",
                )}
              >
                {p.short}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

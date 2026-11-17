"use client";

import { useState, type CSSProperties } from "react";

import { ChipTabs } from "@/shared/components/ChipTabs";
import { formatKsh } from "@/shared/format/format";

import "./CategoryBreakdown.css";

export type Slice = { name: string; cents: number };

const SIDES = [
  { value: "out", label: "Money out" },
  { value: "in", label: "Money in" },
] as const;

/** Where money went, or came from, as ranked bars with each category's share. */
export function CategoryBreakdown({
  slices,
}: {
  slices: { in: Slice[]; out: Slice[] };
}) {
  const [side, setSide] = useState<"in" | "out">("out");
  const shown = slices[side];
  const total = shown.reduce((sum, slice) => sum + slice.cents, 0);
  const largest = Math.max(1, ...shown.map((slice) => slice.cents));

  return (
    <div className="flex flex-col gap-4">
      <ChipTabs
        label="Show"
        chips={SIDES}
        value={side}
        onChange={(value) => setSide(value as "in" | "out")}
      />
      {shown.length === 0 ? (
        <p className="opacity-75">
          Nothing confirmed {side === "out" ? "going out" : "coming in"} yet.
        </p>
      ) : (
        <ol key={side} className="flex flex-col gap-3.5">
          {shown.map((slice, row) => {
            const share = Math.round((slice.cents / total) * 100);
            return (
              <li key={slice.name} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="truncate font-medium">{slice.name}</span>
                  <span className="shrink-0 text-small tabular-nums">
                    {formatKsh(slice.cents)}
                    <span className="ml-2 font-mono text-tiny opacity-60">
                      {share}%
                    </span>
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-current/10">
                  <div
                    className="category-bar h-full rounded-full bg-(--pumpkin) data-[side=in]:bg-(--money-in)"
                    data-side={side}
                    style={
                      {
                        width: `${(slice.cents / largest) * 100}%`,
                        "--row": row,
                      } as CSSProperties
                    }
                  />
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

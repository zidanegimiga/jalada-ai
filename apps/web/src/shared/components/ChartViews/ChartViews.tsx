"use client";

import { useState, type ReactNode } from "react";

import { ChipTabs } from "@/shared/components/ChipTabs";

import "./ChartViews.css";

export type ChartView = { value: string; label: string; content: ReactNode };

/**
 * The same figures drawn several ways, one at a time, with chips to choose between them.
 * Each view is drawn by the server and handed in ready, so switching costs nothing.
 */
export function ChartViews({
  label,
  views,
}: {
  /** Read out for the chips, such as "Show the months as". */
  label: string;
  views: ChartView[];
}) {
  const [chosen, setChosen] = useState(views[0]?.value ?? "");
  const view =
    views.find((candidate) => candidate.value === chosen) ?? views[0];
  if (!view) return null;
  return (
    <div className="flex flex-col gap-4">
      <ChipTabs
        label={label}
        chips={views.map(({ value, label: name }) => ({ value, label: name }))}
        value={view.value}
        onChange={setChosen}
      />
      {/* A new key replays the view's entrance each time it is chosen. */}
      <div key={view.value} className="chart-view">
        {view.content}
      </div>
    </div>
  );
}

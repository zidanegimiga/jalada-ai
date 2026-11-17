"use client";

import { useLayoutEffect, useRef } from "react";

import { cn } from "@/shared/styles/cn";

type Chip = { value: string; label: string };

type ChipTabsProps = {
  /** Read out for the group, such as "Direction". */
  label: string;
  chips: readonly Chip[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

/**
 * One choice from a few, as chips on a track. A highlight slides behind the chosen chip;
 * its place is measured, since chips are as wide as their words.
 */
export function ChipTabs({
  label,
  chips,
  value,
  onChange,
  disabled,
}: ChipTabsProps) {
  const track = useRef<HTMLDivElement>(null);
  const highlight = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const chosen = track.current?.querySelector<HTMLElement>(
      '[aria-pressed="true"]',
    );
    const mark = highlight.current;
    if (!chosen || !mark) return;
    mark.style.width = `${chosen.offsetWidth}px`;
    mark.style.translate = `${chosen.offsetLeft}px 0`;
  }, [value]);

  return (
    <div
      ref={track}
      role="group"
      aria-label={label}
      className="relative flex w-fit max-w-full gap-1 overflow-x-auto rounded-full bg-muted p-1"
    >
      <span
        ref={highlight}
        aria-hidden="true"
        className="absolute inset-y-1 left-0 rounded-full bg-foreground shadow-raised transition-[translate,width] duration-500 ease-[cubic-bezier(0.34,1.3,0.64,1)] motion-reduce:transition-none"
      />
      {chips.map((chip) => {
        const active = chip.value === value;
        return (
          <button
            key={chip.value}
            type="button"
            aria-pressed={active}
            disabled={disabled}
            onClick={() => onChange(chip.value)}
            className={cn(
              "relative min-h-tap shrink-0 rounded-full px-4 text-small font-medium whitespace-nowrap transition-colors duration-300",
              active
                ? "text-background"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {chip.label}
          </button>
        );
      })}
    </div>
  );
}

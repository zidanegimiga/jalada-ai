"use client";

import { Popover } from "@base-ui/react/popover";
import {
  CalendarDays,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useId, useState } from "react";

import { cn } from "@/shared/styles/cn";
import { CONTROL, CONTROL_LABEL, POPUP } from "@/shared/styles/controls";

const SHORT = new Intl.DateTimeFormat("en-KE", {
  month: "short",
  timeZone: "UTC",
});
const LONG = new Intl.DateTimeFormat("en-KE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

/** "2026-11" as a date in UTC, or null for anything else. */
function parse(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})$/.exec(value);
  return match
    ? new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1))
    : null;
}

function key(year: number, monthIndex: number): string {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}`;
}

type MonthPickerProps = {
  label: string;
  /** "YYYY-MM", or "" for every month. */
  value: string;
  onChange: (value: string) => void;
  /** Shown when no month is picked. */
  emptyLabel?: string;
  disabled?: boolean;
  /** A pill as wide as its words, for a filter bar. The label is kept for screen readers. */
  compact?: boolean;
};

/** Picks one month, or none, from a grid that opens under the control. */
export function MonthPicker({
  label,
  value,
  onChange,
  emptyLabel = "All months",
  disabled,
  compact = false,
}: MonthPickerProps) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const picked = parse(value);

  function pick(next: string) {
    onChange(next);
    setOpen(false);
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <div className={cn("flex flex-col gap-2", compact && "w-fit")}>
        <label htmlFor={id} className={compact ? "sr-only" : CONTROL_LABEL}>
          {label}
        </label>
        <Popover.Trigger
          id={id}
          disabled={disabled}
          className={
            compact
              ? "flex min-h-tap items-center gap-2 rounded-full bg-foreground pr-3 pl-4 font-medium text-background transition-[scale,opacity] active:scale-[0.97] disabled:opacity-50"
              : CONTROL
          }
        >
          <CalendarDays aria-hidden="true" className="size-icon shrink-0" />
          <span
            className={cn(
              "flex-1 truncate",
              !picked && !compact && "text-muted-foreground",
            )}
          >
            {picked ? LONG.format(picked) : emptyLabel}
          </span>
          {compact && (
            <ChevronDown
              aria-hidden="true"
              className="size-4 opacity-70 transition-transform in-data-popup-open:rotate-180"
            />
          )}
        </Popover.Trigger>
      </div>
      <Popover.Portal>
        <Popover.Positioner sideOffset={6} align="start" className="z-50">
          <Popover.Popup
            aria-label={`Choose a ${label.toLowerCase()}`}
            className={cn(POPUP, "w-72 p-3")}
          >
            <MonthGrid picked={picked} onPick={pick} emptyLabel={emptyLabel} />
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}

/** Only rendered while open, so "today" is read in the browser, never while prerendering. */
function MonthGrid({
  picked,
  onPick,
  emptyLabel,
}: {
  picked: Date | null;
  onPick: (value: string) => void;
  emptyLabel: string;
}) {
  const now = new Date();
  const thisYear = now.getFullYear();
  const [year, setYear] = useState(picked?.getUTCFullYear() ?? thisYear);
  const [direction, setDirection] = useState(0);

  function turn(step: number) {
    setDirection(step);
    setYear((current) => current + step);
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <button
          type="button"
          aria-label="Previous year"
          onClick={() => turn(-1)}
          className="flex size-tap items-center justify-center rounded-full hover:bg-muted"
        >
          <ChevronLeft aria-hidden="true" className="size-icon" />
        </button>
        <p aria-live="polite" className="text-lead font-bold tabular-nums">
          {year}
        </p>
        <button
          type="button"
          aria-label="Next year"
          onClick={() => turn(1)}
          disabled={year >= thisYear}
          className="flex size-tap items-center justify-center rounded-full hover:bg-muted disabled:opacity-30"
        >
          <ChevronRight aria-hidden="true" className="size-icon" />
        </button>
      </div>
      <div
        key={year}
        className={cn(
          "grid grid-cols-3 gap-1.5 motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300",
          direction > 0 && "motion-safe:slide-in-from-right-4",
          direction < 0 && "motion-safe:slide-in-from-left-4",
        )}
      >
        {Array.from({ length: 12 }, (_, index) => {
          const date = new Date(Date.UTC(year, index));
          const future =
            year > thisYear || (year === thisYear && index > now.getMonth());
          const selected =
            picked?.getUTCFullYear() === year && picked.getUTCMonth() === index;
          return (
            <button
              key={index}
              type="button"
              aria-pressed={selected}
              disabled={future}
              onClick={() => onPick(key(year, index))}
              className={cn(
                "flex min-h-tap items-center justify-center rounded-control font-medium transition-colors disabled:opacity-30",
                selected
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted",
              )}
            >
              <span aria-hidden="true">{SHORT.format(date)}</span>
              <span className="sr-only">{LONG.format(date)}</span>
            </button>
          );
        })}
      </div>
      <button
        type="button"
        onClick={() => onPick("")}
        className="min-h-tap rounded-control border border-border font-medium hover:bg-muted"
      >
        {emptyLabel}
      </button>
    </div>
  );
}

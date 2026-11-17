"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";

import { cn } from "@/shared/styles/cn";

import { addDays, formatDay, today, weeksOf } from "./calendar";

const MONTH = new Intl.DateTimeFormat("en-KE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const DAY = new Intl.DateTimeFormat("en-KE", {
  dateStyle: "full",
  timeZone: "UTC",
});
const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const MOVES: Record<string, number> = {
  ArrowLeft: -1,
  ArrowRight: 1,
  ArrowUp: -7,
  ArrowDown: 7,
};

type CalendarGridProps = {
  picked: Date | null;
  allowFuture: boolean;
  onPick: (day: Date) => void;
};

/**
 * One month of days. Only rendered while open, so "today" is read in the browser. Arrow keys
 * move between days and across months.
 */
export function CalendarGrid({
  picked,
  allowFuture,
  onPick,
}: CalendarGridProps) {
  const now = today();
  const [focus, setFocus] = useState(picked ?? now);
  const grid = useRef<HTMLDivElement>(null);
  const year = focus.getUTCFullYear();
  const month = focus.getUTCMonth();
  const latest = allowFuture ? null : now;

  function move(to: Date) {
    if (latest && to > latest) return;
    setFocus(to);
    requestAnimationFrame(() =>
      grid.current
        ?.querySelector<HTMLButtonElement>(`[data-day="${formatDay(to)}"]`)
        ?.focus(),
    );
  }

  function onKeyDown(event: KeyboardEvent) {
    const step = MOVES[event.key];
    if (step === undefined) return;
    event.preventDefault();
    move(addDays(focus, step));
  }

  function turn(step: number) {
    const target = new Date(Date.UTC(year, month + step, 1));
    setFocus(latest && target > latest ? latest : target);
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <button
          type="button"
          aria-label="Previous month"
          onClick={() => turn(-1)}
          className="flex size-tap items-center justify-center rounded-full hover:bg-muted"
        >
          <ChevronLeft aria-hidden="true" className="size-icon" />
        </button>
        <p aria-live="polite" className="font-bold">
          {MONTH.format(new Date(Date.UTC(year, month, 1)))}
        </p>
        <button
          type="button"
          aria-label="Next month"
          onClick={() => turn(1)}
          disabled={
            latest !== null && new Date(Date.UTC(year, month + 1, 1)) > latest
          }
          className="flex size-tap items-center justify-center rounded-full hover:bg-muted disabled:opacity-30"
        >
          <ChevronRight aria-hidden="true" className="size-icon" />
        </button>
      </div>
      <div
        ref={grid}
        role="group"
        aria-label={MONTH.format(new Date(Date.UTC(year, month, 1)))}
        onKeyDown={onKeyDown}
        key={`${year}-${month}`}
        className="grid grid-cols-7 gap-0.5 text-center motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300"
      >
        {WEEKDAYS.map((day) => (
          <span
            key={day}
            aria-hidden="true"
            className="py-1 text-tiny text-muted-foreground"
          >
            {day}
          </span>
        ))}
        {weeksOf(year, month).map((day) => {
          const key = formatDay(day);
          const outside = day.getUTCMonth() !== month;
          const future = latest !== null && day > latest;
          const selected = picked !== null && formatDay(picked) === key;
          const isToday = formatDay(now) === key;
          return (
            <button
              key={key}
              type="button"
              data-day={key}
              aria-label={DAY.format(day)}
              aria-pressed={selected}
              tabIndex={formatDay(focus) === key ? 0 : -1}
              disabled={future}
              onClick={() => onPick(day)}
              className={cn(
                "flex h-10 items-center justify-center rounded-full text-small tabular-nums transition-colors disabled:opacity-25",
                outside && "text-muted-foreground",
                selected
                  ? "bg-primary font-bold text-primary-foreground"
                  : "hover:bg-muted",
                isToday && !selected && "ring-1 ring-foreground ring-inset",
              )}
            >
              {day.getUTCDate()}
            </button>
          );
        })}
      </div>
    </div>
  );
}

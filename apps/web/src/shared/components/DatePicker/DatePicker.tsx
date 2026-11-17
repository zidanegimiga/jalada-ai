"use client";

import { Popover } from "@base-ui/react/popover";
import { CalendarDays } from "lucide-react";
import { useId, useState } from "react";

import { cn } from "@/shared/styles/cn";
import { CONTROL, CONTROL_LABEL, POPUP } from "@/shared/styles/controls";

import { formatDay, parseDay } from "./calendar";
import { CalendarGrid } from "./CalendarGrid";

const SHOWN = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

type DatePickerProps = {
  label: string;
  /** Sent with the form as "YYYY-MM-DD". */
  name: string;
  defaultValue?: string;
  placeholder?: string;
  /** Allow days after today. Money that has moved never has a future date. */
  allowFuture?: boolean;
};

/** A day from a calendar that opens under the control, instead of the phone's date input. */
export function DatePicker({
  label,
  name,
  defaultValue = "",
  placeholder = "Choose a date",
  allowFuture = false,
}: DatePickerProps) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(defaultValue);
  const picked = parseDay(value);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <div className="flex flex-col gap-2">
        <label htmlFor={id} className={CONTROL_LABEL}>
          {label}
        </label>
        <Popover.Trigger id={id} className={CONTROL}>
          <CalendarDays aria-hidden="true" className="size-icon shrink-0" />
          <span
            className={cn(
              "flex-1 truncate",
              !picked && "text-muted-foreground",
            )}
          >
            {picked ? SHOWN.format(picked) : placeholder}
          </span>
        </Popover.Trigger>
        <input type="hidden" name={name} value={value} />
      </div>
      <Popover.Portal>
        <Popover.Positioner sideOffset={6} align="start" className="z-50">
          <Popover.Popup
            aria-label={`Choose the ${label.toLowerCase()}`}
            className={cn(POPUP, "w-80 p-3")}
          >
            <CalendarGrid
              picked={picked}
              allowFuture={allowFuture}
              onPick={(day) => {
                setValue(formatDay(day));
                setOpen(false);
              }}
            />
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}

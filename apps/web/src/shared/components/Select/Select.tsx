"use client";

import { Select as Base } from "@base-ui/react/select";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/shared/styles/cn";
import { CONTROL, CONTROL_LABEL, POPUP } from "@/shared/styles/controls";

export type SelectOption = { value: string; label: string };

type SelectProps = {
  label: string;
  options: SelectOption[];
  value?: string | null;
  defaultValue?: string | null;
  onValueChange?: (value: string) => void;
  /** Sent with the form, like a native select's name. */
  name?: string;
  required?: boolean;
  placeholder?: string;
  className?: string;
};

/** A labelled choice from a list, styled like the other controls instead of the phone's own. */
export function Select({
  label,
  options,
  value,
  defaultValue,
  onValueChange,
  name,
  required,
  placeholder = "Choose one",
  className,
}: SelectProps) {
  return (
    <Base.Root
      items={options}
      value={value}
      defaultValue={defaultValue}
      onValueChange={(next) => {
        if (next !== null) onValueChange?.(String(next));
      }}
      name={name}
      required={required}
    >
      <div className={cn("flex flex-col gap-2", className)}>
        <Base.Label className={CONTROL_LABEL}>{label}</Base.Label>
        <Base.Trigger className={CONTROL}>
          <Base.Value
            placeholder={placeholder}
            className="flex-1 truncate data-placeholder:text-muted-foreground"
          />
          <Base.Icon className="transition-transform duration-300 in-data-popup-open:rotate-180">
            <ChevronDown aria-hidden="true" className="size-icon" />
          </Base.Icon>
        </Base.Trigger>
      </div>
      <Base.Portal>
        <Base.Positioner sideOffset={6} className="z-50 outline-none">
          <Base.Popup
            className={cn(
              POPUP,
              "max-h-[min(var(--available-height),20rem)] min-w-(--anchor-width) overflow-y-auto",
            )}
          >
            <Base.List>
              {options.map((option) => (
                <Base.Item
                  key={option.value}
                  value={option.value}
                  className="flex min-h-tap cursor-default items-center gap-3 rounded-control px-3 outline-none select-none data-highlighted:bg-muted data-selected:font-medium"
                >
                  <Base.ItemText className="flex-1">
                    {option.label}
                  </Base.ItemText>
                  <Base.ItemIndicator>
                    <Check
                      aria-hidden="true"
                      className="size-icon text-primary"
                    />
                  </Base.ItemIndicator>
                </Base.Item>
              ))}
            </Base.List>
          </Base.Popup>
        </Base.Positioner>
      </Base.Portal>
    </Base.Root>
  );
}

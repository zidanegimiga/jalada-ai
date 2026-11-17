"use client";

import { Volume2, VolumeX } from "lucide-react";

import { setSoundsOn, useSoundsOn } from "@/shared/sound/sound-setting";
import { cn } from "@/shared/styles/cn";

/** Turns the tap sounds on or off for this device. */
export function SoundChoice() {
  const on = useSoundsOn();
  const Icon = on ? Volume2 : VolumeX;
  return (
    <div className="flex items-center justify-between gap-4">
      <span id="sound-label" className="flex items-center gap-2 font-medium">
        <Icon aria-hidden="true" className="size-icon" />
        Tap sounds
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={on}
        aria-labelledby="sound-label"
        onClick={() => setSoundsOn(!on)}
        className="flex h-tap w-16 shrink-0 items-center justify-center rounded-full"
      >
        <span
          aria-hidden="true"
          className={cn(
            "flex h-8 w-14 items-center rounded-full p-1 transition-colors duration-300",
            on ? "bg-primary" : "bg-muted ring-1 ring-border ring-inset",
          )}
        >
          <span
            className={cn(
              "size-6 rounded-full bg-card shadow-raised transition-[translate] duration-300 ease-[cubic-bezier(0.34,1.4,0.64,1)]",
              on && "translate-x-6",
            )}
          />
        </span>
      </button>
    </div>
  );
}

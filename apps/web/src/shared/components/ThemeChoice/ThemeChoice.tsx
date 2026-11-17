"use client";

import { Moon, Smartphone, Sun } from "lucide-react";

import {
  centreOf,
  switchTheme,
  type ThemeChoice as Choice,
} from "@/shared/theme/theme";
import { useThemeChoice } from "@/shared/theme/useThemeChoice";

const OPTIONS: { value: Choice; label: string; Icon: typeof Sun }[] = [
  { value: "system", label: "Auto", Icon: Smartphone },
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
];

/** Light, dark, or Auto, which follows the phone. */
export function ThemeChoice() {
  const choice = useThemeChoice();

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 font-medium">Appearance</legend>
      <div className="grid grid-cols-3 gap-2">
        {OPTIONS.map(({ value, label, Icon }) => (
          <label
            key={value}
            className="flex min-h-tap cursor-pointer flex-col items-center justify-center gap-1 rounded-control border border-border bg-card px-2 py-3 text-small font-medium transition-colors has-checked:border-foreground has-checked:bg-foreground has-checked:text-background has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-(--focus)"
          >
            <input
              type="radio"
              name="theme"
              value={value}
              checked={choice === value}
              onChange={(event) =>
                switchTheme(value, centreOf(event.currentTarget.parentElement!))
              }
              className="sr-only"
            />
            <Icon aria-hidden="true" className="size-icon" />
            {label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

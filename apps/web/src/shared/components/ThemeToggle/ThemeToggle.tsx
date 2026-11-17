"use client";

import { Moon, Sun } from "lucide-react";

import { centreOf, resolvedTheme, switchTheme } from "@/shared/theme/theme";
import { cn } from "@/shared/styles/cn";

/** Flips between light and dark. The icon shows the theme on screen, set by CSS alone. */
export function ThemeToggle({ className }: { className?: string }) {
  return (
    <button
      type="button"
      aria-label="Switch between light and dark"
      onClick={(event) =>
        switchTheme(
          resolvedTheme() === "dark" ? "light" : "dark",
          centreOf(event.currentTarget),
        )
      }
      className={cn(
        "relative flex size-tap items-center justify-center rounded-full border border-border bg-card text-foreground transition-colors hover:bg-muted",
        className,
      )}
    >
      <Sun
        aria-hidden="true"
        className="size-icon transition-transform duration-500 dark:scale-0 dark:-rotate-90"
      />
      <Moon
        aria-hidden="true"
        className="absolute size-icon scale-0 rotate-90 transition-transform duration-500 dark:scale-100 dark:rotate-0"
      />
    </button>
  );
}

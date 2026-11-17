/** What the person picked. "system" follows the phone. */
export type ThemeChoice = "system" | "light" | "dark";

export const THEME_CHOICES: ThemeChoice[] = ["system", "light", "dark"];

export const THEME_STORAGE_KEY = "jalada-theme";

/** Sent on window whenever the choice changes, so every control showing it can update. */
export const THEME_CHANGED = "jalada-theme-changed";

/** The browser bar colour for each theme: the page background. */
export const THEME_COLOURS = { light: "#fefff6", dark: "#0c0c0a" } as const;

function isChoice(value: unknown): value is ThemeChoice {
  return THEME_CHOICES.includes(value as ThemeChoice);
}

export function readThemeChoice(): ThemeChoice {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    return isChoice(saved) ? saved : "system";
  } catch {
    return "system";
  }
}

/** The theme on screen now, after following the phone if nothing was picked. */
export function resolvedTheme(): "light" | "dark" {
  const chosen = document.documentElement.dataset.theme;
  if (chosen === "light" || chosen === "dark") return chosen;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function paintBrowserBar(choice: ThemeChoice) {
  document.querySelectorAll('meta[name="theme-color"]').forEach((meta) => {
    const media = meta.getAttribute("media") ?? "";
    const forMedia = media.includes("dark") ? "dark" : "light";
    meta.setAttribute(
      "content",
      THEME_COLOURS[choice === "system" ? forMedia : choice],
    );
  });
}

/** Saves the choice and applies it to the page. */
export function setThemeChoice(choice: ThemeChoice) {
  const root = document.documentElement;
  if (choice === "system") delete root.dataset.theme;
  else root.dataset.theme = choice;
  paintBrowserBar(choice);
  try {
    if (choice === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, choice);
  } catch {
    // Private browsing can refuse storage; the choice then lasts until the page closes.
  }
  window.dispatchEvent(new Event(THEME_CHANGED));
}

/**
 * Applies a choice with a circle that grows from `origin` (the button pressed), where the
 * browser supports view transitions and the person has not asked for less motion.
 */
export function switchTheme(
  choice: ThemeChoice,
  origin?: { x: number; y: number },
) {
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!document.startViewTransition || still || !origin) {
    setThemeChoice(choice);
    return;
  }
  const root = document.documentElement;
  root.classList.add("theme-switching");
  const transition = document.startViewTransition(() => setThemeChoice(choice));
  const radius = Math.hypot(
    Math.max(origin.x, innerWidth - origin.x),
    Math.max(origin.y, innerHeight - origin.y),
  );
  transition.ready.then(() => {
    root.animate(
      {
        clipPath: [
          `circle(0px at ${origin.x}px ${origin.y}px)`,
          `circle(${radius}px at ${origin.x}px ${origin.y}px)`,
        ],
      },
      {
        duration: 550,
        easing: "cubic-bezier(0.65, 0, 0.35, 1)",
        pseudoElement: "::view-transition-new(root)",
      },
    );
  });
  transition.finished.finally(() => root.classList.remove("theme-switching"));
}

/** The middle of an element, for `switchTheme`'s circle. */
export function centreOf(element: Element): { x: number; y: number } {
  const box = element.getBoundingClientRect();
  return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
}

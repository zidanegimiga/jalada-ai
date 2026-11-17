import { useSyncExternalStore } from "react";

import { THEME_CHANGED, readThemeChoice, type ThemeChoice } from "./theme";

function subscribe(onChange: () => void) {
  window.addEventListener(THEME_CHANGED, onChange);
  // Another tab changed it.
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(THEME_CHANGED, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** The saved theme choice. The server does not know it, so it renders "system". */
export function useThemeChoice(): ThemeChoice {
  return useSyncExternalStore(subscribe, readThemeChoice, () => "system");
}

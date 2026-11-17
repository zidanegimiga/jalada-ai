import { useSyncExternalStore } from "react";

export const SOUND_STORAGE_KEY = "jalada-sound";

/** Sent on window when the setting changes, so every control showing it can update. */
const SOUND_CHANGED = "jalada-sound-changed";

/** Sounds are on unless the person turned them off on this device. */
export function soundsOn(): boolean {
  try {
    return localStorage.getItem(SOUND_STORAGE_KEY) !== "off";
  } catch {
    return true;
  }
}

export function setSoundsOn(on: boolean) {
  try {
    if (on) localStorage.removeItem(SOUND_STORAGE_KEY);
    else localStorage.setItem(SOUND_STORAGE_KEY, "off");
  } catch {
    // Private browsing can refuse storage; the setting then lasts until the page closes.
  }
  window.dispatchEvent(new Event(SOUND_CHANGED));
}

function subscribe(onChange: () => void) {
  window.addEventListener(SOUND_CHANGED, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(SOUND_CHANGED, onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function useSoundsOn(): boolean {
  return useSyncExternalStore(subscribe, soundsOn, () => true);
}

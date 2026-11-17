"use client";

import { useEffect } from "react";

import { playClick } from "@/shared/sound/click";
import { soundsOn } from "@/shared/sound/sound-setting";

/** What makes the tap sound: buttons, links, and the labels of choices. */
const PRESSABLE = 'button, [role="button"], [role="switch"], a[href], label';

function pressable(target: EventTarget | null): Element | null {
  const element = target instanceof Element ? target.closest(PRESSABLE) : null;
  if (!element || element.matches(":disabled, [aria-disabled='true']"))
    return null;
  return element;
}

/** One listener for the whole app, so every button sounds the same without wiring each one. */
export function ClickSounds() {
  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (soundsOn() && pressable(event.target)) playClick();
    }
    document.addEventListener("click", onClick, { capture: true });
    return () =>
      document.removeEventListener("click", onClick, { capture: true });
  }, []);
  return null;
}

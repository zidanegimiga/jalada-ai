"use client";

import { useEffect } from "react";

import { SPLASH } from "./config";

/** Plays the loading screen out once the app is ready and the opening has played. */
export function SplashExit() {
  useEffect(() => {
    const root = document.documentElement;
    const splash = document.getElementById("splash");
    if (!splash || root.dataset.splash === "seen") return;

    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wait = still ? 0 : Math.max(0, SPLASH.minimumMs - performance.now());
    const hide = () => {
      root.dataset.splash = "seen";
    };
    const timer = setTimeout(() => {
      try {
        sessionStorage.setItem(SPLASH.storageKey, "1");
      } catch {
        // Private browsing can refuse storage. The screen then shows on each reload.
      }
      if (still) return hide();
      splash.addEventListener("animationend", (event) => {
        if (event.target === splash) hide();
      });
      splash.dataset.state = "leaving";
    }, wait);
    return () => clearTimeout(timer);
  }, []);

  return null;
}

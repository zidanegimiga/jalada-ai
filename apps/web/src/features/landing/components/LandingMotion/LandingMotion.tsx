"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { useEffect, type ReactNode } from "react";

import { MOTIONS, playOpening } from "../../motion";

import "lenis/dist/lenis.css";

gsap.registerPlugin(ScrollTrigger);

/** Calls `start` once the loading screen has left, or at once when there is none. */
function afterSplash(start: () => void): () => void {
  const root = document.documentElement;
  const gone = () =>
    root.dataset.splash === "seen" || !document.getElementById("splash");
  if (gone()) {
    start();
    return () => {};
  }
  const watch = new MutationObserver(() => {
    if (!gone()) return;
    watch.disconnect();
    start();
  });
  watch.observe(root, { attributes: true, attributeFilter: ["data-splash"] });
  return () => watch.disconnect();
}

/**
 * Smooth scrolling and every effect on the landing page. People who ask for less motion get
 * the page as it is written: no smoothing, nothing pinned, nothing hidden.
 */
export function LandingMotion({ children }: { children: ReactNode }) {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>("[data-landing]");
    if (!root) return;
    const media = gsap.matchMedia();

    media.add(
      {
        calm: "(prefers-reduced-motion: no-preference)",
        wide: "(min-width: 768px)",
      },
      (context) => {
        const { calm, wide } = context.conditions as {
          calm: boolean;
          wide: boolean;
        };
        if (!calm) {
          root.dataset.ready = "true";
          return;
        }

        const lenis = new Lenis({ anchors: { offset: -72 }, lerp: 0.09 });
        lenis.on("scroll", ScrollTrigger.update);
        const tick = (time: number) => lenis.raf(time * 1000);
        gsap.ticker.add(tick);
        gsap.ticker.lagSmoothing(0);

        const undo: (() => void)[] = [];
        for (const element of root.querySelectorAll<HTMLElement>(
          "[data-motion]",
        )) {
          for (const name of (element.dataset.motion ?? "").split(" ")) {
            const done = MOTIONS[name]?.(element, { wide });
            if (done) undo.push(done);
          }
        }
        const opening = playOpening(root).pause();
        root.dataset.ready = "true";
        undo.push(afterSplash(() => opening.play()));

        // Pins are measured with the fallback font; measure again once Onest has loaded.
        document.fonts.ready.then(() => ScrollTrigger.refresh());

        return () => {
          for (const done of undo) done();
          gsap.ticker.remove(tick);
          lenis.destroy();
        };
      },
    );
    return () => media.revert();
  }, []);

  return children;
}

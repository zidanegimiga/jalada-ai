"use client";

import { gsap } from "gsap";
import { useEffect, useRef, useState } from "react";

const PRESSABLE = "a, button, summary, [role='button']";

/**
 * A dot that follows the pointer and inverts what is under it. Over a section with
 * data-cursor it grows into a pumpkin disc with that word; over links and buttons it opens
 * into a ring. Only for a mouse or trackpad: on touch screens there is nothing to follow.
 */
export function Cursor() {
  const dot = useRef<HTMLDivElement>(null);
  const [label, setLabel] = useState("");
  const [state, setState] = useState<"hidden" | "dot" | "press" | "label">(
    "hidden",
  );

  useEffect(() => {
    const element = dot.current;
    if (!element || !matchMedia("(pointer: fine)").matches) return;
    document.documentElement.dataset.pointer = "custom";
    const x = gsap.quickTo(element, "x", {
      duration: 0.35,
      ease: "power3.out",
    });
    const y = gsap.quickTo(element, "y", {
      duration: 0.35,
      ease: "power3.out",
    });

    const move = (event: PointerEvent) => {
      x(event.clientX);
      y(event.clientY);
      const target = event.target instanceof Element ? event.target : null;
      // Only parts of the landing page name a word, never the page root.
      const word =
        target?.closest<HTMLElement>("[data-landing] [data-cursor]")?.dataset
          .cursor ?? "";
      if (target?.closest(PRESSABLE)) {
        setState("press");
      } else if (word) {
        setLabel(word);
        setState("label");
      } else {
        setState("dot");
      }
    };
    const leave = () => setState("hidden");
    window.addEventListener("pointermove", move);
    document.documentElement.addEventListener("pointerleave", leave);
    return () => {
      delete document.documentElement.dataset.pointer;
      window.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", leave);
    };
  }, []);

  return (
    <div
      ref={dot}
      className="landing-cursor"
      data-state={state}
      aria-hidden="true"
    >
      <span>{label}</span>
    </div>
  );
}

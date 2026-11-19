// Effects that bring text and figures into view.
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { type Motion, EASE, onView, all, one } from "./motion-kit";

/** Lines of a heading slide up from behind a mask. */
export const lines: Motion = (element) => {
  gsap.from(all(element, "[data-line] > span"), {
    yPercent: 115,
    duration: 1.2,
    ease: EASE,
    stagger: 0.09,
    scrollTrigger: onView(element),
  });
};

/** Words light up one after another while the paragraph crosses the screen. */
export const words: Motion = (element) => {
  gsap.fromTo(
    all(element, "[data-word]"),
    { opacity: 0.16 },
    {
      opacity: 1,
      ease: "none",
      stagger: 0.1,
      scrollTrigger: {
        trigger: element,
        start: "top 78%",
        end: "bottom 50%",
        scrub: true,
      },
    },
  );
};

/** The element, or its children with data-stagger, rise into place. */
export const rise: Motion = (element) => {
  const targets = element.hasAttribute("data-stagger")
    ? Array.from(element.children)
    : element;
  gsap.from(targets, {
    y: 56,
    opacity: 0,
    duration: 1.1,
    ease: EASE,
    stagger: 0.08,
    scrollTrigger: onView(element),
  });
};

/** Counts up to data-to when it comes into view. */
export const count: Motion = (element) => {
  const to = Number(element.dataset.to ?? 0);
  const shown = { value: 0 };
  element.textContent = "0";
  gsap.to(shown, {
    value: to,
    duration: 1.8,
    ease: "power3.out",
    scrollTrigger: onView(element, "top 90%"),
    onUpdate: () => {
      element.textContent = Math.round(shown.value).toLocaleString("en-KE");
    },
  });
};

/** The closing word grows from under the fold. */
export const grow: Motion = (element) => {
  gsap.fromTo(
    element,
    { yPercent: 40, scale: 0.9 },
    {
      yPercent: 0,
      scale: 1,
      ease: "none",
      scrollTrigger: {
        trigger: element,
        start: "top bottom",
        end: "bottom bottom",
        scrub: true,
      },
    },
  );
};

/** The example conversation plays once, the first time it comes into view. */
export const conversation: Motion = (element) => {
  const steps = all(element, "[data-say]");
  const typing = one(element, "[data-typing]");
  const answer = all(element, "[data-answer] [data-word]");
  const play = gsap.timeline({ paused: true });
  play.from(steps[0], { y: 24, opacity: 0, duration: 0.6, ease: EASE });
  if (typing)
    play.fromTo(typing, { opacity: 0 }, { opacity: 1, duration: 0.2 }, "+=0.2");
  for (const step of steps.slice(1, -2)) {
    play.from(
      step,
      { x: -16, opacity: 0, duration: 0.5, ease: EASE },
      "+=0.35",
    );
  }
  if (typing)
    play.to(typing, { opacity: 0, height: 0, duration: 0.25 }, "+=0.4");
  play.from(steps.at(-2) ?? [], { y: 16, opacity: 0, duration: 0.4 });
  play.from(answer, { opacity: 0, duration: 0.25, stagger: 0.03 }, "<");
  play.from(
    steps.at(-1) ?? [],
    { y: 30, opacity: 0, duration: 0.8, ease: EASE },
    "+=0.2",
  );
  ScrollTrigger.create({
    trigger: element,
    start: "top 65%",
    once: true,
    onEnter: () => play.play(),
  });
};

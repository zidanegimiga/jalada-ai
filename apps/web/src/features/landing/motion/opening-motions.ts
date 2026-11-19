// The opening: evidence that follows the pointer, then gathers into a ledger.
import { gsap } from "gsap";

import { type Motion, EASE, all, one } from "./motion-kit";

/** Things move with the pointer, each by its data-depth. */
export const depth: Motion = (element, { wide }) => {
  if (!wide) return;
  const layers = all(element, "[data-depth]").map((layer) => ({
    x: gsap.quickTo(layer, "x", { duration: 1, ease: "power3.out" }),
    y: gsap.quickTo(layer, "y", { duration: 1, ease: "power3.out" }),
    amount: Number(layer.dataset.depth) * 28,
  }));
  const move = (event: PointerEvent) => {
    const box = element.getBoundingClientRect();
    const dx = (event.clientX - box.left) / box.width - 0.5;
    const dy = (event.clientY - box.top) / box.height - 0.5;
    for (const layer of layers) {
      layer.x(dx * layer.amount);
      layer.y(dy * layer.amount);
    }
  };
  element.addEventListener("pointermove", move);
  return () => element.removeEventListener("pointermove", move);
};

/**
 * The opening: scattered evidence flies into the middle and becomes a ledger. On phones
 * the ledger simply sits under the heading.
 */
export const gather: Motion = (element, { wide }) => {
  if (!wide) return;
  const stage = one(element, "[data-stage]");
  const heading = one(element, "[data-heading]");
  const ledger = one(element, "[data-ledger]");
  if (!stage || !heading || !ledger) return;
  const chips = all(element, "[data-chip]");
  const toMiddle = (chip: HTMLElement) => {
    const box = chip.getBoundingClientRect();
    const area = stage.getBoundingClientRect();
    return {
      x: area.left + area.width / 2 - (box.left + box.width / 2),
      y: area.top + area.height / 2 - (box.top + box.height / 2),
    };
  };
  gsap
    .timeline({
      scrollTrigger: {
        trigger: element,
        start: "top top",
        end: "+=120%",
        pin: true,
        scrub: 1,
        invalidateOnRefresh: true,
      },
    })
    .to(all(element, "[data-cue]"), { opacity: 0, duration: 0.2 }, 0)
    .to(
      heading,
      { yPercent: -30, opacity: 0, ease: "power2.in", duration: 0.45 },
      0,
    )
    .to(
      chips,
      {
        x: (_index, chip: HTMLElement) => toMiddle(chip).x,
        y: (_index, chip: HTMLElement) => toMiddle(chip).y,
        rotate: 0,
        scale: 0.35,
        opacity: 0,
        ease: "power2.in",
        stagger: 0.05,
        duration: 0.6,
      },
      0.05,
    )
    .fromTo(
      ledger,
      { scale: 0.7, opacity: 0, y: 60 },
      { scale: 1, opacity: 1, y: 0, ease: "power3.out", duration: 0.5 },
      0.45,
    )
    .from(
      all(ledger, "[data-row]"),
      { x: -30, opacity: 0, stagger: 0.06, ease: "power3.out", duration: 0.3 },
      0.65,
    );
};

/** The opening once the loading screen has gone: the heading, then the evidence. */
export function playOpening(root: HTMLElement) {
  const intro = gsap.timeline({ defaults: { ease: EASE } });
  intro
    .from(all(root, "[data-intro-line] > span"), {
      yPercent: 115,
      duration: 1.3,
      stagger: 0.1,
    })
    .from(
      all(root, "[data-intro]"),
      { y: 30, opacity: 0, duration: 1, stagger: 0.08 },
      0.35,
    )
    .from(
      all(root, "[data-pop]"),
      {
        scale: 0.6,
        opacity: 0,
        rotate: -8,
        duration: 1.1,
        stagger: 0.07,
        ease: "back.out(1.6)",
      },
      0.25,
    );
  return intro;
}

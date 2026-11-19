import type { ScrollTrigger } from "gsap/ScrollTrigger";

/**
 * An effect on the landing page. An element asks for one with data-motion="name" (several
 * are separated by spaces), so sections stay plain markup and an effect is changed in one
 * place. See MOTIONS in index.ts.
 *
 * Each runs inside a gsap context, which undoes its tweens. Listeners it adds are removed by
 * the function it returns.
 */
export type MotionContext = { wide: boolean };
export type Motion = (
  element: HTMLElement,
  context: MotionContext,
) => (() => void) | void;

export const EASE = "expo.out";

/** Plays once, when the element is near the bottom of the screen. */
export function onView(
  trigger: Element,
  start = "top 85%",
): ScrollTrigger.Vars {
  return { trigger, start, toggleActions: "play none none none" };
}

export function all(element: Element, selector: string): HTMLElement[] {
  return Array.from(element.querySelectorAll<HTMLElement>(selector));
}

export function one(element: Element, selector: string): HTMLElement | null {
  return element.querySelector<HTMLElement>(selector);
}

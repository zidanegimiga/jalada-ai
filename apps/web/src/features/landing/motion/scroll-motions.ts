// Effects tied to how far the page has scrolled.
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { type Motion, all, one } from "./motion-kit";

/** Moves slower or faster than the page. data-speed above 0 lags, below 0 leads. */
export const parallax: Motion = (element) => {
  const speed = Number(element.dataset.speed ?? 0.15);
  gsap.fromTo(
    element,
    { y: () => -speed * window.innerHeight * 0.5 },
    {
      y: () => speed * window.innerHeight * 0.5,
      ease: "none",
      scrollTrigger: {
        trigger: element.parentElement ?? element,
        start: "top bottom",
        end: "bottom top",
        scrub: true,
        invalidateOnRefresh: true,
      },
    },
  );
};

/** A band that runs on its own and speeds up, or turns round, with the scroll. */
export const ribbon: Motion = (element) => {
  const track = one(element, "[data-track]");
  if (!track) return;
  const run = gsap.to(track, {
    xPercent: -50,
    ease: "none",
    duration: Number(element.dataset.duration ?? 28),
    repeat: -1,
  });
  ScrollTrigger.create({
    trigger: element,
    start: "top bottom",
    end: "bottom top",
    onUpdate: (self) => {
      const push = 1 + Math.min(Math.abs(self.getVelocity()) / 350, 5);
      gsap.to(run, {
        timeScale: self.direction * push,
        duration: 0.2,
        overwrite: true,
      });
      gsap.to(run, { timeScale: self.direction, duration: 1.2, delay: 0.2 });
    },
  });
};

/** Pins the section and slides its track sideways while the page scrolls down. */
export const sideways: Motion = (element, { wide }) => {
  const track = one(element, "[data-track]");
  if (!wide || !track) return;
  const bar = one(element, "[data-progress]");
  const distance = () => Math.max(0, track.scrollWidth - window.innerWidth);
  const slide = gsap.to(track, {
    x: () => -distance(),
    ease: "none",
    scrollTrigger: {
      trigger: element,
      start: "top top",
      end: () => `+=${distance()}`,
      pin: true,
      scrub: 0.8,
      invalidateOnRefresh: true,
      onUpdate: (self) => bar && gsap.set(bar, { scaleX: self.progress }),
    },
  });
  // Each panel's picture drifts against the slide, for depth.
  for (const picture of all(element, "[data-drift]")) {
    gsap.fromTo(
      picture,
      { xPercent: 12 },
      {
        xPercent: -12,
        ease: "none",
        scrollTrigger: {
          trigger: picture.closest("[data-panel]") ?? picture,
          containerAnimation: slide,
          start: "left right",
          end: "right left",
          scrub: true,
        },
      },
    );
  }
};

/** Cards stick in turn; each one sinks back as the next slides over it. */
export const stack: Motion = (element) => {
  const cards = all(element, "[data-card]");
  cards.forEach((card, index) => {
    const next = cards[index + 1];
    if (!next) return;
    gsap.to(card, {
      scale: 0.9,
      yPercent: -4,
      ease: "none",
      scrollTrigger: {
        trigger: next,
        start: "top bottom",
        end: "top 20%",
        scrub: true,
      },
    });
  });
};

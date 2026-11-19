"use client";

import { useEffect, useState } from "react";

/**
 * Which of the sections is being read, whether the pill should show, and how far down the
 * page is, from 0 to 1. The pill shows while scrolling down past the first screen, and hides
 * on the way up and over the footer.
 */
export function useScrollSpy(ids: string[]) {
  const [active, setActive] = useState("");
  const [shown, setShown] = useState(false);
  const [progress, setProgress] = useState(0);
  const key = ids.join(" ");

  useEffect(() => {
    const sections = key
      .split(" ")
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => section !== null);
    let last = window.scrollY;
    let frame = 0;

    const check = () => {
      frame = 0;
      const now = window.scrollY;
      const page = document.documentElement.scrollHeight - window.innerHeight;
      const middle = window.innerHeight * 0.45;
      const current = sections.findLast(
        (section) => section.getBoundingClientRect().top <= middle,
      );
      setActive(current?.id ?? "");
      setProgress(page > 0 ? Math.min(now / page, 1) : 0);
      const nearEnd = page - now < window.innerHeight * 0.6;
      if (Math.abs(now - last) > 6) {
        setShown(now > last && now > window.innerHeight * 0.9 && !nearEnd);
        last = now;
      }
      if (nearEnd) setShown(false);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(check);
    };
    check();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [key]);

  return { active, shown, progress };
}

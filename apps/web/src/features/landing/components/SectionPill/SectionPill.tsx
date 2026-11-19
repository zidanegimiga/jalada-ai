"use client";

import { useEffect, useRef, useState } from "react";

import { SECTIONS } from "../../site";
import { useScrollSpy } from "../../hooks/useScrollSpy";

/**
 * A floating bar of the page's sections. It rises while reading down, past the opening, and
 * steps aside on the way back up, when the header returns. The section being read is
 * marked, and a ring fills as the page goes by.
 */
export function SectionPill() {
  const { active, shown, progress } = useScrollSpy(SECTIONS.map((s) => s.id));
  const list = useRef<HTMLDivElement>(null);
  const [mark, setMark] = useState({ left: 0, width: 0 });

  useEffect(() => {
    const link = list.current?.querySelector<HTMLElement>(
      `[data-id="${active}"]`,
    );
    if (!link || !list.current) return;
    setMark({ left: link.offsetLeft, width: link.offsetWidth });
    // On phones the bar scrolls sideways; keep the marked section in view.
    list.current.scrollTo({
      left:
        link.offsetLeft - list.current.clientWidth / 2 + link.offsetWidth / 2,
      behavior: "smooth",
    });
  }, [active]);

  return (
    <nav
      aria-label="Page sections"
      data-shown={shown}
      className="landing-pill fixed inset-x-0 bottom-4 z-40 flex justify-center px-3"
    >
      <div className="flex max-w-full items-center gap-1 rounded-full bg-(--l-ink) p-1.5 text-(--l-paper) shadow-[0_18px_40px_-12px_rgb(0_0_0/0.55)]">
        <svg
          viewBox="0 0 36 36"
          aria-hidden="true"
          className="size-11 shrink-0 -rotate-90"
        >
          <circle
            cx="18"
            cy="18"
            r="14"
            fill="none"
            stroke="rgb(255 255 255 / 0.15)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="14"
            fill="none"
            stroke="var(--l-pumpkin)"
            strokeWidth="3"
            strokeLinecap="round"
            pathLength={1}
            strokeDasharray="1"
            strokeDashoffset={1 - progress}
          />
        </svg>
        <div ref={list} className="landing-pill-list relative overflow-x-auto">
          <span
            aria-hidden="true"
            className="landing-pill-mark absolute top-0 left-0 h-full rounded-full bg-(--l-pumpkin)"
            style={{ translate: `${mark.left}px 0`, width: mark.width }}
          />
          <ul className="relative flex">
            {SECTIONS.map((section) => (
              <li key={section.id} className="shrink-0">
                <a
                  href={`#${section.id}`}
                  data-id={section.id}
                  aria-current={active === section.id ? "true" : undefined}
                  className="landing-pill-link flex min-h-tap items-center rounded-full px-4 text-small font-medium whitespace-nowrap"
                >
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}

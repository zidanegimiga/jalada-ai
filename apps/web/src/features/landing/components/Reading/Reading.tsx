"use client";

import { useEffect, useState } from "react";

import { FIELDS, MESSAGE } from "../../content";
import { Eyebrow } from "../Eyebrow";
import { Lines } from "../SplitText";

/**
 * One M-Pesa message and what the app takes from it. Pointing at a field lights up where
 * it came from; left alone, the fields take turns.
 */
export function Reading() {
  const [active, setActive] = useState(FIELDS[0].id);
  const [held, setHeld] = useState(false);

  useEffect(() => {
    if (held || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = setInterval(() => {
      setActive((current) => {
        const index = FIELDS.findIndex((field) => field.id === current);
        return FIELDS[(index + 1) % FIELDS.length].id;
      });
    }, 2200);
    return () => clearInterval(timer);
  }, [held]);

  return (
    <section
      id="reading"
      data-tone="light"
      className="bg-(--l-paper) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto grid max-w-[90rem] gap-16 lg:grid-cols-[1fr_1.1fr] lg:gap-24">
        <div>
          <Eyebrow number="03">Reading</Eyebrow>
          <h2
            data-motion="lines"
            className="mt-8 text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
          >
            <Lines
              lines={[
                "Read,",
                <span key="b" className="text-(--l-rust)">
                  not guessed.
                </span>,
              ]}
            />
          </h2>
          <p className="mt-8 max-w-[40ch] text-lead text-(--l-quiet)">
            Every amount it keeps can be pointed to in the original. When a
            photo is too blurred to read, it says so and asks you, instead of
            making a number up.
          </p>
        </div>

        <div
          data-motion="rise"
          data-cursor="Point"
          onPointerEnter={() => setHeld(true)}
          onPointerLeave={() => setHeld(false)}
          className="grid gap-5"
        >
          <figure className="rounded-[2rem] bg-(--l-ink) p-6 text-(--l-paper) md:p-9">
            <figcaption className="flex items-center justify-between font-mono text-tiny tracking-[0.16em] text-(--l-quiet-on-ink) uppercase">
              <span>Forwarded message</span>
              <span>MPESA</span>
            </figcaption>
            <p className="mt-6 text-[clamp(1.125rem,2vw,1.5rem)] leading-relaxed">
              {MESSAGE.map((part, index) =>
                "field" in part ? (
                  <mark
                    key={index}
                    data-on={part.field === active}
                    className="landing-mark"
                  >
                    {part.text}
                  </mark>
                ) : (
                  <span key={index}>{part.text}</span>
                ),
              )}
            </p>
          </figure>

          <ul
            aria-label="What it takes from the message"
            className="grid gap-2"
          >
            {FIELDS.map((field) => (
              <li key={field.id}>
                <button
                  type="button"
                  aria-pressed={field.id === active}
                  onPointerEnter={() => setActive(field.id)}
                  onFocus={() => {
                    setHeld(true);
                    setActive(field.id);
                  }}
                  onBlur={() => setHeld(false)}
                  onClick={() => setActive(field.id)}
                  className="landing-field flex min-h-14 w-full items-center justify-between gap-4 rounded-full px-6 text-left"
                >
                  <span className="font-mono text-tiny tracking-[0.16em] uppercase">
                    {field.label}
                  </span>
                  <span className="text-body font-bold tabular-nums">
                    {field.value}
                  </span>
                </button>
              </li>
            ))}
            <li className="flex min-h-14 items-center justify-between gap-4 rounded-full border border-dashed border-(--l-line) px-6">
              <span className="font-mono text-tiny tracking-[0.16em] uppercase">
                Category
              </span>
              <span className="text-small">
                Groceries, from your past choices for Naivas
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}

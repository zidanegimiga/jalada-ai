"use client";

import { gsap } from "gsap";
import Link from "next/link";
import { useEffect, useRef, type ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

type Props = {
  href: string;
  children: ReactNode;
  tone?: "pumpkin" | "ink" | "paper" | "line";
  size?: "md" | "lg";
  className?: string;
};

const TONES = {
  pumpkin: "bg-(--l-pumpkin) text-(--l-ink)",
  ink: "bg-(--l-ink) text-(--l-paper)",
  paper: "bg-(--l-paper) text-(--l-ink)",
  line: "border border-current text-current",
};

/**
 * A pill link whose words roll up under the pointer, and which leans towards the pointer
 * while it is near.
 */
export function RollLink({
  href,
  children,
  tone = "pumpkin",
  size = "md",
  className,
}: Props) {
  const link = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const element = link.current;
    const calm = matchMedia(
      "(prefers-reduced-motion: no-preference) and (pointer: fine)",
    );
    if (!element || !calm.matches) return;
    const x = gsap.quickTo(element, "x", { duration: 0.5, ease: "power3.out" });
    const y = gsap.quickTo(element, "y", { duration: 0.5, ease: "power3.out" });
    const lean = (event: PointerEvent) => {
      const box = element.getBoundingClientRect();
      x((event.clientX - box.left - box.width / 2) * 0.3);
      y((event.clientY - box.top - box.height / 2) * 0.4);
    };
    const settle = () => {
      gsap.to(element, {
        x: 0,
        y: 0,
        duration: 0.9,
        ease: "elastic.out(1, 0.4)",
      });
    };
    element.addEventListener("pointermove", lean);
    element.addEventListener("pointerleave", settle);
    return () => {
      element.removeEventListener("pointermove", lean);
      element.removeEventListener("pointerleave", settle);
    };
  }, []);

  const inPage = href.startsWith("#");
  const classes = cn(
    "landing-roll group/roll inline-flex min-h-tap items-center justify-center gap-2 rounded-full font-medium",
    size === "lg" ? "h-16 px-8 text-lead" : "h-12 px-6 text-body",
    TONES[tone],
    className,
  );
  const words = (
    <span
      className="landing-roll-words"
      data-text={typeof children === "string" ? children : ""}
    >
      <span>{children}</span>
    </span>
  );

  return inPage ? (
    <a ref={link} href={href} className={classes} data-roll={tone}>
      {words}
    </a>
  ) : (
    <Link ref={link} href={href} className={classes} data-roll={tone}>
      {words}
    </Link>
  );
}

"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { NAV } from "../../content";
import { RollLink } from "../RollLink";

/**
 * Slides away while reading down and comes back on the way up. Its colours follow the
 * section under it, so it stays readable over dark bands.
 */
export function SiteHeader() {
  const [hidden, setHidden] = useState(false);
  const [tone, setTone] = useState("light");
  const [top, setTop] = useState(true);

  useEffect(() => {
    let last = window.scrollY;
    let frame = 0;
    const check = () => {
      frame = 0;
      const now = window.scrollY;
      setTop(now < 24);
      if (Math.abs(now - last) > 6) {
        setHidden(now > last && now > 160);
        last = now;
      }
      const under = document
        .elementsFromPoint(window.innerWidth / 2, 36)
        .find((element) => !element.closest("[data-site-header]"))
        ?.closest<HTMLElement>("[data-tone]");
      setTone(under?.dataset.tone ?? "light");
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
  }, []);

  return (
    <header
      data-site-header=""
      data-hidden={hidden}
      data-tone={tone}
      data-top={top}
      className="landing-header fixed inset-x-0 top-0 z-40"
    >
      <div className="mx-auto flex h-18 max-w-[90rem] items-center justify-between gap-4 px-4 md:px-8">
        <Link
          href="/"
          className="flex min-h-tap items-center gap-2.5 text-lead font-bold"
        >
          <Image
            src="/mark.webp"
            alt=""
            width={36}
            height={36}
            unoptimized
            className="size-9 rounded-control"
          />
          <span className="max-sm:sr-only">Jalada AI</span>
        </Link>
        <nav
          aria-label="Sections"
          className="hidden items-center gap-1 lg:flex"
        >
          {NAV.map((item) => (
            <a key={item.href} href={item.href} className="landing-nav-link">
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <Link href="/signin" className="landing-nav-link">
            Sign in
          </Link>
          <RollLink href="/signup" className="h-11 px-5 text-small">
            Start your records
          </RollLink>
        </div>
      </div>
    </header>
  );
}

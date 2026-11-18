"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { CSSProperties, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

import { currentIndex, DESTINATIONS, type Destination } from "../navigation";
import { NAV_BACK, NAV_FORWARD } from "../PageTransition";

/**
 * A floating pill at the bottom, within reach of a thumb. A pumpkin highlight slides to the
 * current page. `toCheck` is the badge on To check, streamed in from the server.
 */
export function AppNav({
  toCheck,
  places = DESTINATIONS,
}: {
  toCheck?: ReactNode;
  places?: Destination[];
}) {
  const current = currentIndex(usePathname(), places);
  // Four tabs are narrower, so the bar still fits a 360px phone.
  const tab = places.length > 3 ? "5rem" : "6rem";
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-[calc(env(safe-area-inset-bottom)+0.75rem)] z-40 flex justify-center px-gutter lg:hidden"
      // Its own layer in page transitions, so pages slide under it, never over it.
      style={{ viewTransitionName: "app-nav" }}
    >
      {/* The page fades out just above the bar, so nothing scrolls into it edge to edge. */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-x-0 bottom-0 -z-10 h-36 bg-linear-to-t from-background from-30% to-transparent"
      />
      <ul
        className="relative grid grid-flow-col rounded-full bg-foreground p-1.5 text-background shadow-float ring-1 ring-black/10 dark:bg-muted dark:text-foreground dark:ring-white/12"
        style={{ "--current": current, "--tab": tab } as CSSProperties}
      >
        <li
          aria-hidden="true"
          className={cn(
            "absolute inset-y-1.5 left-1.5 w-(--tab) rounded-full bg-primary transition-[translate,opacity] duration-500 ease-[cubic-bezier(0.34,1.4,0.64,1)] motion-reduce:transition-none",
            current < 0 && "opacity-0",
          )}
          style={{
            translate: `calc(var(--current) * 100%) 0`,
            // Its own name, so a page change glides it to the new page.
            viewTransitionName: "nav-highlight",
          }}
        />
        {places.map(({ href, label, Icon }, index) => {
          const here = index === current;
          return (
            <li key={href} className="relative">
              <Link
                href={href}
                aria-current={here ? "page" : undefined}
                transitionTypes={[index > current ? NAV_FORWARD : NAV_BACK]}
                // A layer above the gliding highlight, so the label stays readable.
                style={{
                  viewTransitionName: `nav-link-${index}`,
                  viewTransitionClass: "nav-link",
                }}
                className={cn(
                  "group flex h-14 w-(--tab) flex-col items-center justify-center gap-0.5 rounded-full text-tiny font-medium transition-[color,scale] duration-200 active:scale-95",
                  // Leaving the highlight turns light at once; arriving waits for it to slide in.
                  here && "text-primary-foreground delay-300",
                )}
              >
                <span
                  className={cn(
                    "flex flex-col items-center gap-0.5 transition-[opacity,translate] duration-300",
                    here
                      ? "-translate-y-0.5"
                      : "opacity-75 group-hover:opacity-100",
                  )}
                >
                  <Icon aria-hidden="true" className="size-icon" />
                  {label}
                </span>
                {href === "/review" && (
                  <span className="absolute top-1 right-5 [--badge-ring:var(--foreground)] dark:[--badge-ring:var(--muted)]">
                    {toCheck}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

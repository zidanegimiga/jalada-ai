"use client";

import { BookOpen, Home, ListChecks, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { CSSProperties, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

import { NAV_BACK, NAV_FORWARD } from "../PageTransition";

type Destination = { href: string; label: string; Icon: LucideIcon };

const LINKS: Destination[] = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/review", label: "To check", Icon: ListChecks },
  { href: "/ledger", label: "Ledger", Icon: BookOpen },
];

/** Which link a path belongs to: /ledger/certificates/1 is still the ledger. */
function currentIndex(pathname: string): number {
  const index = LINKS.findIndex(({ href }) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href),
  );
  return index;
}

/**
 * A floating pill at the bottom, within reach of a thumb. A pumpkin highlight slides to the
 * current page. `toCheck` is the badge on To check, streamed in from the server.
 */
export function AppNav({ toCheck }: { toCheck?: ReactNode }) {
  const current = currentIndex(usePathname());
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-[calc(env(safe-area-inset-bottom)+0.75rem)] z-40 flex justify-center px-gutter"
    >
      <ul
        className="relative grid grid-cols-3 rounded-full bg-foreground p-1.5 text-background shadow-overlay dark:border dark:border-border dark:bg-card dark:text-foreground"
        style={{ "--current": current } as CSSProperties}
      >
        <li
          aria-hidden="true"
          className={cn(
            "absolute inset-y-1.5 left-1.5 w-24 rounded-full bg-primary transition-[translate,opacity] duration-500 ease-[cubic-bezier(0.34,1.4,0.64,1)] motion-reduce:transition-none",
            current < 0 && "opacity-0",
          )}
          style={{
            translate: `calc(var(--current) * 100%) 0`,
            // Its own name, so a page change glides it to the new page.
            viewTransitionName: "nav-highlight",
          }}
        />
        {LINKS.map(({ href, label, Icon }, index) => {
          const here = index === current;
          return (
            <li key={href} className="relative">
              <Link
                href={href}
                aria-current={here ? "page" : undefined}
                transitionTypes={[index > current ? NAV_FORWARD : NAV_BACK]}
                className={cn(
                  "group flex h-14 w-24 flex-col items-center justify-center gap-0.5 rounded-full text-tiny font-medium transition-[color,scale] duration-300 active:scale-95",
                  here && "text-primary-foreground",
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
                {href === "/review" && toCheck}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

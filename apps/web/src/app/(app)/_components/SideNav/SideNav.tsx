"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { ThemeToggle } from "@/shared/components/ThemeToggle";
import { cn } from "@/shared/styles/cn";

import { currentIndex, DESTINATIONS } from "../navigation";
import { NAV_BACK, NAV_FORWARD } from "../PageTransition";

/**
 * The navigation on wide screens: a rail down the left with the brand, the three places and,
 * at the foot, the theme and the account. `toCheck` and `account` stream in from the server.
 */
export function SideNav({
  toCheck,
  account,
}: {
  toCheck?: ReactNode;
  account: ReactNode;
}) {
  const current = currentIndex(usePathname());
  return (
    <nav
      aria-label="Main"
      className="sticky top-0 hidden h-dvh flex-col gap-8 border-r border-border bg-card px-4 py-6 lg:flex"
    >
      <Link
        href="/"
        className="flex min-h-tap items-center gap-3 rounded-control px-2 text-lead font-bold"
      >
        <Image
          src="/mark.webp"
          alt=""
          width={40}
          height={40}
          unoptimized
          className="size-10 rounded-control"
        />
        Jalada AI
      </Link>
      <ul className="flex flex-col gap-1">
        {DESTINATIONS.map(({ href, label, Icon }, index) => {
          const here = index === current;
          return (
            <li key={href} className="relative">
              {here && (
                <span
                  aria-hidden="true"
                  className="absolute inset-0 rounded-control bg-primary"
                  style={{ viewTransitionName: "nav-highlight" }}
                />
              )}
              <Link
                href={href}
                aria-current={here ? "page" : undefined}
                transitionTypes={[index > current ? NAV_FORWARD : NAV_BACK]}
                className={cn(
                  "relative flex min-h-12 items-center gap-3 rounded-control px-3 font-medium transition-colors",
                  here
                    ? "text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon aria-hidden="true" className="size-icon" />
                {label}
                {href === "/review" && (
                  <span className="ml-auto">{toCheck}</span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-auto flex items-center gap-2 border-t border-border pt-4">
        {account}
        <ThemeToggle className="ml-auto" />
      </div>
    </nav>
  );
}

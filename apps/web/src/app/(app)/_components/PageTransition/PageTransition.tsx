"use client";

import { usePathname } from "next/navigation";
import { ViewTransition, type ReactNode } from "react";

import "./page-transitions.css";

/** Transition types the bottom navigation sets, by which way the person moved along it. */
export const NAV_FORWARD = "nav-forward";
export const NAV_BACK = "nav-back";

/**
 * Animates one page out and the next in. Moving right along the navigation slides the page
 * left, moving left slides it right, and any other link lifts the new page in. Other updates,
 * such as data arriving, are not animated. The styles are in page-transitions.css.
 */
export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <ViewTransition
      key={usePathname()}
      default="none"
      enter={{
        [NAV_FORWARD]: "page-from-right",
        [NAV_BACK]: "page-from-left",
        default: "page-rise",
      }}
      exit={{
        [NAV_FORWARD]: "page-to-left",
        [NAV_BACK]: "page-to-right",
        default: "page-fade",
      }}
    >
      {children}
    </ViewTransition>
  );
}

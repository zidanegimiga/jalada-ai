# 0027. Motion on the landing page

Status: Accepted
Date: 2026-11-19
Builds on: 0005 (frontend toolchain), 0024 (web app layout)

## Context
Visitors who are not signed in were sent straight to sign-in, so nobody could find out what Jalada AI does before making an account. The landing page explains it through movement: scattered evidence gathering into one ledger as the page scrolls, steps that slide sideways while the section holds still, a message whose parts light up as you point at them, and an example conversation that plays once.

That needs scroll-linked animation (progress tied to how far the page has scrolled), pinned sections, smooth scrolling that the scroll effects can follow, and a reliable way to undo all of it when the page is left. CSS scroll-driven animations cover simple reveals but not pinning, horizontal sections or timelines across several elements, and Safari support is incomplete.

## Options considered
1. **CSS and IntersectionObserver only.** No dependency, but pinning, scrubbed timelines and velocity effects would be hand-built and fragile.
2. **Motion (formerly Framer Motion).** Good for component transitions, weaker for long pinned scroll timelines, and it wraps elements in its own components.
3. **GSAP with ScrollTrigger, and Lenis for smooth scrolling.** The common pairing for this kind of page. GSAP is free for commercial use, including every plugin. Lenis keeps native scrolling, so the page stays accessible and anchor links work.

## Decision
Option 3, used only by the landing feature (`features/landing`). Every effect is a named function in a registry (`features/landing/motion`), and markup asks for one with `data-motion="name"`. One component sets up Lenis and runs the registry inside `gsap.matchMedia`, which undoes everything when the page is left.

Rules:
- People who ask for less motion get none: no smooth scrolling, nothing pinned, nothing hidden. The page reads in full without the script.
- Pinned and sideways effects run on wide screens only. Phones get the same content stacked.
- The custom pointer only appears for a mouse or trackpad.
- The signed-in app does not use GSAP or Lenis.

## Consequences
- About 52 kB of compressed script (GSAP 28, ScrollTrigger 18, Lenis 5) on the landing page only; signed-in pages do not load it.
- Adding an effect means one function in the registry and one attribute in the markup. A test fails if the markup names an effect the registry does not have, or the registry keeps one nothing uses.
- Scroll effects are measured from layout, so a change in a section's size can need a look at the pinned sections on wide screens.

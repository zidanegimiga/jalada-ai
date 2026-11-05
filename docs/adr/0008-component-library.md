# 0008. shadcn/ui for components

Status: Accepted
Date: 2026-11-05
Amends: 0005

## Context
Decision 0005 chose Tailwind and rejected component kits such as Material UI, because they are heavy to download and make every app look alike. Building every input, dialog, menu and sheet by hand is slow, and accessibility details such as focus handling and keyboard support are easy to get wrong. The visual direction is now set: the Onest font, a black, pumpkin, ivory and flax palette, large rounded cards and pill-shaped buttons.

## Options considered
1. **Build every component by hand on Tailwind.** Full control, but slow, and accessibility is ours to get right each time.
2. **A packaged kit such as Material UI or Chakra UI.** Fast to start, but the downloads are large and restyling them to our look means fighting their defaults.
3. **shadcn/ui.** Not installed as a package. Its command line tool copies each component's source into `src/components/ui/`, styled with Tailwind and built on an accessible primitives library. We own and edit the code, and only the components we add are shipped.

For the primitives under shadcn:
1. **Radix UI.** The long-standing choice, but its development has slowed.
2. **Base UI.** From the team behind Radix and Material UI, actively developed, and now shadcn's default.

## Decision
shadcn/ui with Base UI primitives and lucide icons, themed through CSS variables in `src/app/globals.css`. Onest is loaded with `next/font`, so it is self-hosted and needs no request to Google at runtime.

## Consequences
- Components are our code. Upgrades are not automatic: we re-run the shadcn tool or edit by hand.
- The palette lives in one place. Text on pumpkin and flax is black, because white on pumpkin fails contrast.
- Buttons are at least 40px tall and 48px by default, so they are easy to tap on small phones.
- Light and dark themes follow the phone's system setting through `prefers-color-scheme`, so there is no theme library and no flash of the wrong theme on load. Every text colour pair meets the WCAG AA contrast ratio of 4.5 to 1 (WCAG is the Web Content Accessibility Guidelines). A manual switch can be added later with a small client component.

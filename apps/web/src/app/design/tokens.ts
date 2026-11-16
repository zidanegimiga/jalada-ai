/** The design tokens in globals.css, listed for the /design page. A test checks that
 * each one is still defined there. */

export const COLOURS = [
  "background",
  "foreground",
  "card",
  "primary",
  "secondary",
  "muted",
  "muted-foreground",
  "border",
  "destructive",
  "money-in",
  "focus",
] as const;

// Class names are written out in full, so Tailwind generates each of them.
export const TYPE = [
  {
    name: "display",
    className: "text-display",
    use: "Page titles",
    sample: "To check",
  },
  {
    name: "total",
    className: "text-total",
    use: "A month's total",
    sample: "KSh 45,000.00",
  },
  {
    name: "amount",
    className: "text-amount",
    use: "The amount on a card",
    sample: "KSh 1,250.00",
  },
  {
    name: "title",
    className: "text-title",
    use: "Section and card headings",
    sample: "Recent",
  },
  {
    name: "lead",
    className: "text-lead",
    use: "Intro lines and names",
    sample: "Nothing to check.",
  },
  {
    name: "body",
    className: "text-body",
    use: "Everything else",
    sample: "Paid to SAMPLE MART",
  },
  {
    name: "small",
    className: "text-small",
    use: "Details under a name",
    sample: "Food · 4 Nov 2026",
  },
] as const;

export const RADII = [
  { name: "card", use: "Cards and panels" },
  { name: "inset", use: "Notes inside a card" },
  { name: "control", use: "Inputs and selects" },
] as const;

export const SPACING = [
  { name: "gutter", use: "Page side margin" },
  { name: "card", use: "Inside a card" },
  { name: "section", use: "Between sections" },
  { name: "tap", use: "Smallest tap target" },
] as const;

export const ICONS = [
  { name: "icon", use: "In lists and buttons" },
  { name: "icon-lg", use: "In the bottom bar" },
] as const;

export const SHADOWS = [
  { name: "raised", use: "Sheets and menus" },
  { name: "overlay", use: "Dialogs" },
] as const;

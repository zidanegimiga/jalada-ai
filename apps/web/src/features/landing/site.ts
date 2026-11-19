/** Where the landing page's links go, and who made it. */

/** The sections, in page order. The header lists some; the pill at the bottom lists all. */
export const SECTIONS = [
  { id: "why", label: "Why", inHeader: false },
  { id: "offer", label: "What it does", inHeader: true },
  { id: "how", label: "How", inHeader: true },
  { id: "reading", label: "Reading", inHeader: false },
  { id: "ask", label: "Ask", inHeader: true },
  { id: "privacy", label: "Privacy", inHeader: true },
  { id: "filing", label: "Filing", inHeader: false },
  { id: "questions", label: "Questions", inHeader: false },
];

export const NAV = SECTIONS.filter((section) => section.inHeader).map(
  (section) => ({ label: section.label, href: `#${section.id}` }),
);

export const CREDIT = {
  name: "Zidane Gimiga",
  href: "https://github.com/zidanegimiga",
};

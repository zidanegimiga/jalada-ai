import type { ReactNode } from "react";

/**
 * Small drawings, 64 by 64, one per kind of evidence or result. Lines use the current text
 * colour; --glyph-fill and --glyph-paper colour the shapes, so one drawing works on any band.
 */
const FILL = "var(--glyph-fill)";
const PAPER = "var(--glyph-paper)";

export const GLYPHS: Record<string, ReactNode> = {
  mpesa: (
    <>
      <rect x="18" y="5" width="28" height="54" rx="7" fill={PAPER} />
      <path d="M22 15h20v17a3 3 0 0 1-3 3H28l-6 5z" fill={FILL} />
      <path d="M27 21h11M27 26h7" />
      <circle cx="32" cy="51" r="1.6" fill="currentColor" />
    </>
  ),
  statement: (
    <>
      <path d="M14 8h28l8 8v40H14z" fill={PAPER} />
      <path d="M42 8v8h8" />
      <rect
        x="19"
        y="20"
        width="26"
        height="6"
        rx="1.5"
        fill={FILL}
        stroke="none"
      />
      <path d="M19 33h12M37 33h8M19 40h10M37 40h8M19 47h14M37 47h8" />
    </>
  ),
  receipt: (
    <>
      <path d="M16 6h32v50l-4-3-4 3-4-3-4 3-4-3-4 3-4-3-4 3z" fill={PAPER} />
      <path d="M22 16h20M22 23h14M22 30h17" />
      <rect
        x="22"
        y="38"
        width="20"
        height="7"
        rx="1.5"
        fill={FILL}
        stroke="none"
      />
    </>
  ),
  payslip: (
    <>
      <rect x="12" y="10" width="40" height="44" rx="4" fill={PAPER} />
      <circle cx="21" cy="20" r="4" fill={FILL} stroke="none" />
      <path d="M29 18h15M29 23h9M18 32h28M18 38h28" />
      <rect
        x="30"
        y="43"
        width="16"
        height="6"
        rx="1.5"
        fill={FILL}
        stroke="none"
      />
    </>
  ),
  certificate: (
    <>
      <rect x="10" y="10" width="44" height="34" rx="3" fill={PAPER} />
      <path d="M17 19h22M17 25h16M17 31h12" />
      <circle cx="43" cy="38" r="8" fill={FILL} />
      <path d="M39 45l-3 12 7-4 7 4-3-12" fill={FILL} />
    </>
  ),
  note: (
    <>
      <path d="M12 14l34-4 6 38-34 4z" fill={FILL} />
      <path d="M20 24l20-2.4M21 31l17-2M22 38l12-1.4" />
      <path d="M44 50l12-26 4 2-12 26-5 3z" fill={PAPER} />
    </>
  ),
  chat: (
    <>
      <path
        d="M8 14a6 6 0 0 1 6-6h36a6 6 0 0 1 6 6v24a6 6 0 0 1-6 6H26l-12 10V44h0a6 6 0 0 1-6-6z"
        fill={PAPER}
      />
      <rect
        x="16"
        y="16"
        width="14"
        height="18"
        rx="2"
        fill={FILL}
        stroke="none"
      />
      <path d="M35 20h13M35 26h9" />
    </>
  ),
  mail: (
    <>
      <rect x="8" y="16" width="48" height="34" rx="4" fill={PAPER} />
      <path d="M8 20l24 17 24-17" />
      <rect
        x="40"
        y="6"
        width="16"
        height="16"
        rx="2"
        fill={FILL}
        transform="rotate(12 48 14)"
      />
    </>
  ),
  drawer: (
    <>
      <path d="M18 14h24l-2 10H20z" fill={FILL} transform="rotate(-6 30 19)" />
      <rect x="8" y="22" width="48" height="32" rx="4" fill={PAPER} />
      <path d="M8 36h48M26 29h12M26 45h12" />
    </>
  ),
  ledger: (
    <>
      <path d="M10 12h20a4 4 0 0 1 4 4v38a4 4 0 0 0-4-4H10z" fill={PAPER} />
      <path d="M54 12H38a4 4 0 0 0-4 4v38a4 4 0 0 1 4-4h16z" fill={FILL} />
      <path d="M15 22h13M15 29h13M15 36h9M40 22h9M40 29h9" />
    </>
  ),
  month: (
    <>
      <rect x="8" y="10" width="48" height="44" rx="5" fill={PAPER} />
      <rect
        x="15"
        y="34"
        width="6"
        height="13"
        rx="1"
        fill={FILL}
        stroke="none"
      />
      <rect
        x="25"
        y="24"
        width="6"
        height="23"
        rx="1"
        fill="currentColor"
        stroke="none"
      />
      <rect
        x="35"
        y="29"
        width="6"
        height="18"
        rx="1"
        fill={FILL}
        stroke="none"
      />
      <rect
        x="45"
        y="18"
        width="6"
        height="29"
        rx="1"
        fill="currentColor"
        stroke="none"
      />
    </>
  ),
  check: (
    <>
      <circle cx="32" cy="32" r="22" fill={FILL} />
      <path d="M21 33l7 7 15-16" strokeWidth="4" />
    </>
  ),
  workbook: (
    <>
      <rect x="10" y="10" width="44" height="44" rx="4" fill={PAPER} />
      <path d="M10 22h44M10 34h44M10 46h44M24 10v44M39 10v44" />
      <rect x="25" y="35" width="13" height="10" fill={FILL} stroke="none" />
    </>
  ),
  ask: (
    <>
      <path
        d="M10 16a6 6 0 0 1 6-6h32a6 6 0 0 1 6 6v22a6 6 0 0 1-6 6H30l-10 9v-9h-4a6 6 0 0 1-6-6z"
        fill={FILL}
      />
      <path d="M27 21a5 5 0 1 1 7 4.6c-1.4.6-2 1.6-2 3V30" />
      <circle cx="32" cy="36" r="1.6" fill="currentColor" />
    </>
  ),
};

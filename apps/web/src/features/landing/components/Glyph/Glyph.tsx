import { GLYPHS } from "../../art/glyph-shapes";

type Props = {
  name: keyof typeof GLYPHS;
  className?: string;
};

/** One of the landing page's small drawings, by name. Decoration only. */
export function Glyph({ name, className }: Props) {
  return (
    <svg
      viewBox="0 0 64 64"
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {GLYPHS[name]}
    </svg>
  );
}

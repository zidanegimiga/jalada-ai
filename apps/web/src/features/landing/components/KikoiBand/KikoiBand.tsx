/**
 * Stripes after the woven kikoi cloth worn along the Kenyan coast, in the app's own colours.
 * The pattern repeats across the band, with a fringe of short threads at each edge.
 */
const STRIPES: [colour: string, width: number][] = [
  ["var(--l-pumpkin)", 54],
  ["var(--l-ink)", 9],
  ["var(--l-flax)", 24],
  ["var(--l-ink)", 9],
  ["var(--l-forest)", 42],
  ["var(--l-paper)", 12],
  ["var(--l-forest)", 12],
  ["var(--l-flax)", 30],
  ["var(--l-rust)", 18],
  ["var(--l-ink)", 6],
  ["var(--l-pumpkin)", 24],
  ["var(--l-paper)", 9],
];

const REPEAT = STRIPES.reduce((total, [, width]) => total + width, 0);

/** Where each stripe starts, worked out once. */
const PLACED = STRIPES.map(([colour, width], index) => ({
  colour,
  width,
  x: STRIPES.slice(0, index).reduce((total, [, w]) => total + w, 0),
}));

export function KikoiBand({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className={className}
      width="100%"
      height="48"
    >
      <defs>
        <pattern
          id="kikoi"
          width={REPEAT}
          height="48"
          patternUnits="userSpaceOnUse"
        >
          {PLACED.map((stripe) => (
            <rect
              key={stripe.x}
              x={stripe.x}
              y="4"
              width={stripe.width}
              height="40"
              fill={stripe.colour}
            />
          ))}
          {Array.from({ length: Math.floor(REPEAT / 4) }, (_, index) => (
            <g key={`fringe-${index}`} stroke="var(--l-flax)" strokeWidth="1">
              <line x1={index * 4 + 2} y1="0" x2={index * 4 + 2} y2="4" />
              <line x1={index * 4 + 2} y1="44" x2={index * 4 + 2} y2="48" />
            </g>
          ))}
        </pattern>
      </defs>
      <rect width="100%" height="48" fill="url(#kikoi)" />
    </svg>
  );
}

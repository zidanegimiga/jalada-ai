type Props = {
  /** Which way the teeth point: down hangs off the band above, up rises from the one below. */
  facing?: "down" | "up";
  className?: string;
};

const TOOTH = 24;

/**
 * The torn, toothed edge of a till receipt, joining two bands of colour. It takes the
 * colour of the band it belongs to from the text colour.
 */
export function ReceiptEdge({ facing = "down", className }: Props) {
  const teeth = Array.from(
    { length: 1440 / TOOTH },
    () => `l${TOOTH / 2} 14 l${TOOTH / 2} -14`,
  ).join(" ");
  return (
    <svg
      viewBox="0 0 1440 14"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      className={className}
      style={facing === "up" ? { rotate: "180deg" } : undefined}
    >
      <path d={`M0 0 ${teeth} V0 Z`} fill="currentColor" />
    </svg>
  );
}

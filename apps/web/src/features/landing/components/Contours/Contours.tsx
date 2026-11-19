/**
 * Flowing contour lines, like a map of hills, drawn behind a section. Each line is a smooth
 * wave whose height and phase shift a little from the one above, so they nest like terrain.
 * Worked out on the server, the same every time.
 */
function wave(row: number, lines: number): string {
  const y = 40 + row * (520 / lines);
  const lift = 26 + 18 * Math.sin(row * 0.7);
  const shift = row * 37;
  const points = Array.from({ length: 9 }, (_, step) => {
    const x = step * 150;
    const rise =
      Math.sin((x + shift) / 190) * lift +
      Math.cos((x - shift) / 310) * lift * 0.6;
    return [x, y + rise] as const;
  });
  return points.reduce((path, [x, y], index) => {
    if (index === 0) return `M${x} ${y.toFixed(1)}`;
    const [px, py] = points[index - 1];
    const mid = (px + x) / 2;
    return `${path} C${mid} ${py.toFixed(1)} ${mid} ${y.toFixed(1)} ${x} ${y.toFixed(1)}`;
  }, "");
}

type Props = { lines?: number; className?: string };

export function Contours({ lines = 14, className }: Props) {
  return (
    <svg
      viewBox="0 0 1200 600"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      {Array.from({ length: lines }, (_, row) => (
        <path
          key={row}
          d={wave(row, lines)}
          fill="none"
          stroke="currentColor"
          strokeWidth={row % 4 === 0 ? 1.4 : 0.8}
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}

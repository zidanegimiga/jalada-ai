/**
 * Lines from each thing sent, through the app in the middle, out to each thing given back.
 * They are drawn as the section scrolls (the "draw" effect). Wide screens only.
 */
export function Threads({ from, to }: { from: number; to: number }) {
  const row = (index: number, count: number) =>
    72 + (index * 856) / (count - 1);
  const into = Array.from({ length: from }, (_, index) => {
    const y = row(index, from);
    return `M0 ${y} C60 ${y} 60 500 100 500`;
  });
  const out = Array.from({ length: to }, (_, index) => {
    const y = row(index, to);
    return `M100 500 C140 500 140 ${y} 200 ${y}`;
  });
  return (
    <div className="relative hidden lg:block">
      <svg
        data-motion="draw"
        viewBox="0 0 200 1000"
        preserveAspectRatio="none"
        aria-hidden="true"
        focusable="false"
        className="absolute inset-x-0 top-12 bottom-0 h-[calc(100%-3rem)] w-full"
      >
        {[...into, ...out].map((d, index) => (
          <path
            key={index}
            d={d}
            fill="none"
            stroke="var(--l-ink)"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
            pathLength={1}
          />
        ))}
      </svg>
      <span className="absolute top-[calc(50%+1.5rem)] left-1/2 grid size-24 -translate-1/2 place-items-center rounded-full bg-(--l-ink) font-mono text-tiny tracking-[0.2em] text-(--l-pumpkin) uppercase">
        Jalada
      </span>
    </div>
  );
}

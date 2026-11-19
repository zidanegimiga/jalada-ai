import { SPLIT } from "../../offer";

/**
 * One invented month of money in, as a single bar split by what it was for. Support from
 * family and moves between your own accounts are not income, so they are kept apart.
 */
export function MoneySplit() {
  return (
    <figure className="mt-24 rounded-[2rem] bg-(--l-ink) p-6 text-(--l-paper) md:p-10">
      <figcaption className="grid gap-2 md:grid-cols-[1fr_auto] md:items-end">
        <span className="text-[clamp(1.75rem,3vw,2.75rem)] leading-none font-bold tracking-tight">
          Money in is not all income.
        </span>
        <span className="font-mono text-tiny tracking-[0.16em] text-(--l-quiet-on-ink) uppercase">
          An example month, KES 145,000 in
        </span>
      </figcaption>
      <div
        data-motion="split"
        className="mt-8 flex h-16 gap-1 overflow-hidden rounded-full md:h-20"
        role="img"
        aria-label={SPLIT.map((part) => `${part.label} ${part.share}%`).join(
          ", ",
        )}
      >
        {SPLIT.map((part) => (
          <span
            key={part.label}
            data-share={part.share}
            className="h-full origin-left rounded-full"
            style={{ flexGrow: part.share, background: part.tone }}
          />
        ))}
      </div>
      <ul className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-4">
        {SPLIT.map((part) => (
          <li key={part.label} className="flex items-start gap-3">
            <span
              className="mt-1.5 size-3 shrink-0 rounded-full ring-1 ring-white/30"
              style={{ background: part.tone }}
            />
            <span>
              <span className="block text-title tabular-nums">
                {part.share}%
              </span>
              <span className="block text-small text-(--l-quiet-on-ink)">
                {part.label}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </figure>
  );
}

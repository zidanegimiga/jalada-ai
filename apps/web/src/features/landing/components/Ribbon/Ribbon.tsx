import { RIBBON } from "../../content";

/** The kinds of evidence, running past. Written twice so the loop has no seam. */
export function Ribbon() {
  const run = [...RIBBON, ...RIBBON];
  return (
    <section
      data-motion="ribbon"
      data-tone="dark"
      aria-label="What you can send"
      className="overflow-hidden bg-(--l-ink) py-7 text-(--l-paper) md:py-10"
    >
      <ul className="sr-only">
        {RIBBON.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <div data-track="" aria-hidden="true" className="flex w-max">
        {[0, 1].map((copy) => (
          <div key={copy} className="flex shrink-0 items-center">
            {run.map((item, index) => (
              <span
                key={index}
                className="flex items-center text-[clamp(2rem,5vw,4.5rem)] font-bold tracking-tight whitespace-nowrap"
              >
                <span className="px-6 md:px-10">{item}</span>
                <span className="size-3 rounded-full bg-(--l-pumpkin) md:size-4" />
              </span>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

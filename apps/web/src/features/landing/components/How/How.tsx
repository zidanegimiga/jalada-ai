import { STEPS } from "../../content";
import { Eyebrow } from "../Eyebrow";
import { Lines } from "../SplitText";

/** A small picture of each step, drawn from shapes rather than screenshots. */
function Picture({ index, detail }: { index: number; detail: string[] }) {
  const tones = [
    "bg-(--l-pumpkin) text-(--l-ink)",
    "bg-(--l-flax) text-(--l-ink)",
    "bg-(--l-paper) text-(--l-ink)",
  ];
  return (
    <div
      data-drift=""
      className="relative flex h-full min-h-56 items-center justify-center"
    >
      <span
        aria-hidden="true"
        data-ghost={STEPS[index].number}
        className="landing-ghost absolute text-[clamp(10rem,22vw,20rem)] leading-none text-white/[0.06]"
      />
      <ul className="relative flex max-w-xs flex-wrap justify-center gap-3">
        {detail.map((item, position) => (
          <li
            key={item}
            className={`rounded-full px-5 py-3 text-body font-medium ${tones[(index + position) % tones.length]}`}
            style={{
              rotate: `${(position % 2 ? 1 : -1) * (3 + position * 2)}deg`,
            }}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * The four steps. On wide screens the section holds still and the steps slide across as
 * the page scrolls; on phones they stack.
 */
export function How() {
  return (
    <section
      id="how"
      data-motion="sideways"
      data-tone="dark"
      data-cursor="Scroll"
      className="relative overflow-hidden bg-(--l-ink) text-(--l-paper)"
    >
      <div
        data-track=""
        className="flex flex-col md:h-dvh md:w-max md:flex-row md:items-stretch"
      >
        <div className="flex shrink-0 flex-col justify-center px-4 pt-28 pb-12 md:w-[42vw] md:px-12 md:py-0 lg:px-20">
          <Eyebrow number="03">How it works</Eyebrow>
          <h2
            data-motion="lines"
            className="mt-8 text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
          >
            <Lines
              lines={[
                "Four steps.",
                <span key="b" className="text-(--l-pumpkin)">
                  One tap from you.
                </span>,
              ]}
            />
          </h2>
          <p className="mt-8 max-w-[40ch] text-lead text-(--l-quiet-on-ink)">
            Every piece of evidence goes through the same short path, and each
            run is written down, so any entry can be traced back to where it
            came from.
          </p>
        </div>

        {STEPS.map((step, index) => (
          <article
            key={step.number}
            data-panel=""
            className="grid shrink-0 gap-8 border-t border-white/10 px-4 py-14 md:w-[70vw] md:grid-cols-2 md:items-center md:border-t-0 md:border-l md:px-14 md:py-0 lg:w-[58vw]"
          >
            <div>
              <p className="font-mono text-tiny tracking-[0.2em] text-(--l-pumpkin) uppercase">
                Step {step.number}
              </p>
              <h3 className="mt-4 text-[clamp(3rem,6vw,5.5rem)] leading-none font-bold tracking-[-0.04em]">
                {step.title}
              </h3>
              <p className="mt-6 max-w-[36ch] text-lead text-(--l-quiet-on-ink)">
                {step.text}
              </p>
            </div>
            <Picture index={index} detail={step.detail} />
          </article>
        ))}
        <div
          aria-hidden="true"
          className="hidden shrink-0 md:block md:w-[12vw]"
        />
      </div>

      <div className="absolute inset-x-12 bottom-10 hidden h-px bg-white/15 md:block">
        <div
          data-progress=""
          className="h-full origin-left scale-x-0 bg-(--l-pumpkin)"
        />
      </div>
    </section>
  );
}

import { QUESTIONS } from "../../content";
import { Eyebrow } from "../Eyebrow";
import { Lines } from "../SplitText";

/** Common questions, each opening in place. */
export function Questions() {
  return (
    <section
      id="questions"
      data-tone="light"
      className="bg-(--l-paper-deep) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto grid max-w-[90rem] gap-14 lg:grid-cols-[1fr_1.5fr]">
        <div>
          <Eyebrow number="07">Questions</Eyebrow>
          <h2
            data-motion="lines"
            className="mt-8 text-[clamp(2.75rem,5vw,5rem)] leading-[0.92] font-bold tracking-[-0.04em]"
          >
            <Lines lines={["Asked", "and answered."]} />
          </h2>
        </div>
        <div
          data-motion="rise"
          data-stagger=""
          className="border-t border-(--l-line)"
        >
          {QUESTIONS.map((item) => (
            <details
              key={item.q}
              name="landing-questions"
              className="landing-question group border-b border-(--l-line)"
            >
              <summary className="flex min-h-20 cursor-pointer list-none items-center justify-between gap-6 py-5 text-[clamp(1.25rem,2vw,1.75rem)] font-bold tracking-tight">
                {item.q}
                <span
                  aria-hidden="true"
                  className="landing-plus relative size-10 shrink-0 rounded-full bg-(--l-ink)"
                />
              </summary>
              <p className="max-w-2xl pb-8 text-lead text-(--l-quiet)">
                {item.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

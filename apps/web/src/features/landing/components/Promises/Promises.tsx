import { PROMISES } from "../../content";
import { Eyebrow } from "../Eyebrow";
import { Lines } from "../SplitText";

const TONES: Record<string, string> = {
  ink: "bg-(--l-ink) text-(--l-paper)",
  pumpkin: "bg-(--l-pumpkin) text-(--l-ink)",
  paper: "bg-(--l-paper) text-(--l-ink)",
  flax: "bg-(--l-flax) text-(--l-ink)",
};

/** Four promises about people's data. Each card sticks, and the next slides over it. */
export function Promises() {
  return (
    <section
      id="privacy"
      data-tone="light"
      className="bg-(--l-paper-deep) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto max-w-[90rem]">
        <div className="grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <Eyebrow number="05">Privacy</Eyebrow>
            <h2
              data-motion="lines"
              className="mt-8 text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
            >
              <Lines
                lines={[
                  "Your money.",
                  <span key="b" className="text-(--l-rust)">
                    Your records.
                  </span>,
                ]}
              />
            </h2>
          </div>
          <a
            href="/privacy"
            className="landing-underline min-h-tap self-end text-body font-medium"
          >
            Read the privacy notice
          </a>
        </div>

        <ol data-motion="stack" className="mt-16 grid gap-6 md:mt-24">
          {PROMISES.map((promise, index) => (
            <li
              key={promise.title}
              data-card=""
              className={`landing-stack-card sticky flex min-h-[64vh] origin-top flex-col justify-between gap-10 overflow-hidden rounded-[2.25rem] p-7 md:min-h-[70vh] md:p-14 ${TONES[promise.tone]}`}
              style={{ top: `calc(5.5rem + ${index} * 1.25rem)` }}
            >
              <div className="flex items-start justify-between gap-6">
                <p className="font-mono text-small tracking-[0.2em] uppercase opacity-70">
                  0{index + 1} / 0{PROMISES.length}
                </p>
                <span
                  aria-hidden="true"
                  className="text-[clamp(6rem,16vw,15rem)] leading-[0.75] font-bold tracking-[-0.06em] opacity-10"
                >
                  0{index + 1}
                </span>
              </div>
              <div>
                <h3 className="max-w-3xl text-[clamp(2.25rem,5vw,4.75rem)] leading-[0.95] font-bold tracking-[-0.035em]">
                  {promise.title}
                </h3>
                <p className="mt-6 max-w-[52ch] text-lead opacity-80">
                  {promise.text}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

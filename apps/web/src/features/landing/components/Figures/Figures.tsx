import { FIGURES } from "../../content";
import { Eyebrow } from "../Eyebrow";
import { Lines } from "../SplitText";

/** Filing time, and a few plain facts about the app, counted up. */
export function Figures() {
  return (
    <section
      id="filing"
      data-tone="light"
      className="bg-(--l-paper) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto max-w-[90rem]">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-end">
          <div>
            <Eyebrow number="07">Filing time</Eyebrow>
            <h2
              data-motion="lines"
              className="mt-8 text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
            >
              <Lines
                lines={[
                  "Filing time,",
                  <span key="b" className="text-(--l-rust)">
                    made boring.
                  </span>,
                ]}
              />
            </h2>
          </div>
          <p className="max-w-[46ch] text-lead text-(--l-quiet)">
            At the end of the year your figures come grouped the way the KRA
            iTax return asks for them, in a workbook you can open anywhere. It
            never decides on its own that something is taxable or deductible:
            that stays with you.
          </p>
        </div>

        <dl className="mt-20 grid border-t border-(--l-line) sm:grid-cols-2 lg:grid-cols-4">
          {FIGURES.map((figure) => (
            <div
              key={figure.label}
              data-motion="rise"
              className="landing-figure border-b border-(--l-line) py-8 sm:px-6 sm:[&:nth-child(odd)]:pl-0 lg:border-b-0 lg:[&:not(:first-child)]:border-l lg:[&:not(:first-child)]:pl-6"
            >
              <dt className="sr-only">{figure.label}</dt>
              <dd>
                <span
                  data-motion="count"
                  data-to={figure.value}
                  className="block text-[clamp(4rem,8vw,7.5rem)] leading-none font-bold tracking-[-0.05em] tabular-nums"
                >
                  {figure.value}
                </span>
                <span className="mt-4 block text-title">{figure.label}</span>
                <span className="mt-2 block text-small text-(--l-quiet)">
                  {figure.note}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

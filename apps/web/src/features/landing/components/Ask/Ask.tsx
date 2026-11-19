import { Eyebrow } from "../Eyebrow";
import { Lines, Words } from "../SplitText";

const LOOKUPS = ["Adding up payments", "Transport, October"];

/** The assistant, shown as one example conversation that plays when it scrolls in. */
export function Ask() {
  return (
    <section
      id="ask"
      data-tone="dark"
      data-cursor="Ask"
      className="relative overflow-hidden bg-(--l-ink-soft) px-4 py-28 text-(--l-paper) md:px-8 md:py-40"
    >
      <div
        aria-hidden="true"
        data-motion="parallax"
        data-speed="-0.3"
        className="pointer-events-none absolute -right-[10vw] top-10 text-[clamp(14rem,36vw,34rem)] leading-none font-bold tracking-[-0.06em] text-white/[0.035]"
      >
        ?
      </div>
      <div className="relative mx-auto grid max-w-[90rem] gap-16 lg:grid-cols-[1fr_1fr] lg:items-center lg:gap-24">
        <div>
          <Eyebrow number="04">Ask</Eyebrow>
          <h2
            data-motion="lines"
            className="mt-8 text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
          >
            <Lines
              lines={[
                "Ask your",
                <span key="b" className="text-(--l-pumpkin)">
                  own records.
                </span>,
              ]}
            />
          </h2>
          <p className="mt-8 max-w-[40ch] text-lead text-(--l-quiet-on-ink)">
            Answers come only from what you have sent. Every figure is checked
            against your records before you see it, and any change it suggests
            waits for your tap. On the web, or in your Telegram chat.
          </p>
          <ul
            data-motion="rise"
            data-stagger=""
            className="mt-10 grid max-w-[40ch] gap-3 text-body"
          >
            <li className="flex gap-3">
              <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-(--l-pumpkin)" />
              No tax advice, and no filing on your behalf
            </li>
            <li className="flex gap-3">
              <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-(--l-pumpkin)" />
              Only your records, never anyone else&apos;s
            </li>
            <li className="flex gap-3">
              <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-(--l-pumpkin)" />
              Off until you agree to a model reading them
            </li>
          </ul>
        </div>

        <figure
          data-motion="conversation"
          className="rounded-[2rem] bg-(--l-ink) p-5 md:p-8"
        >
          <figcaption className="font-mono text-tiny tracking-[0.16em] text-(--l-quiet-on-ink) uppercase">
            An example conversation
          </figcaption>
          <div className="mt-6 grid gap-3">
            <p
              data-say=""
              className="ml-auto max-w-[85%] rounded-[1.5rem] rounded-br-md bg-(--l-pumpkin) px-5 py-3.5 text-body text-(--l-ink)"
            >
              How much did I spend on transport in October?
            </p>
            <p
              data-typing=""
              aria-hidden="true"
              className="landing-typing flex gap-1.5 px-2 py-2"
            >
              <span />
              <span />
              <span />
            </p>
            {LOOKUPS.map((lookup) => (
              <p
                key={lookup}
                data-say=""
                className="flex w-fit items-center gap-2 rounded-full bg-white/8 px-4 py-2 font-mono text-tiny tracking-wide text-(--l-quiet-on-ink)"
              >
                <span className="size-1.5 rounded-full bg-(--l-in)" />
                {lookup}
              </p>
            ))}
            <p
              data-say=""
              data-answer=""
              className="max-w-[92%] rounded-[1.5rem] rounded-bl-md bg-(--l-paper) px-5 py-4 text-body text-(--l-ink)"
            >
              <Words text="You spent KES 6,840.00 on transport in October, across 23 payments. The largest share went to Little, KES 4,120.00." />
            </p>
            <div
              data-say=""
              className="mt-2 rounded-[1.5rem] bg-(--l-flax) p-5 text-(--l-ink)"
            >
              <p className="font-mono text-[0.625rem] tracking-[0.16em] uppercase">
                Suggested change
              </p>
              <p className="mt-2 text-body font-medium">
                3 payments to Little are waiting in To check. Put them under
                Transport?
              </p>
              <div className="mt-4 flex gap-2" aria-hidden="true">
                <span className="rounded-full bg-(--l-ink) px-5 py-2.5 text-small font-medium text-(--l-paper)">
                  Confirm
                </span>
                <span className="rounded-full px-5 py-2.5 text-small font-medium ring-1 ring-(--l-ink)/30">
                  Not now
                </span>
              </div>
            </div>
          </div>
        </figure>
      </div>
    </section>
  );
}

import { AUDIENCE, GETS, SENDS } from "../../offer";
import { Eyebrow } from "../Eyebrow";
import { Glyph } from "../Glyph";
import { MoneySplit } from "../MoneySplit";
import { Lines } from "../SplitText";
import { Threads } from "./Threads";

type Item = { glyph: string; title: string; text: string };

function Column({
  heading,
  items,
}: {
  heading: string;
  items: readonly Item[];
}) {
  return (
    <div>
      <h3 className="font-mono text-tiny tracking-[0.2em] uppercase">
        {heading}
      </h3>
      <ul data-motion="rise" data-stagger="" className="mt-6 grid gap-3">
        {items.map((item) => (
          <li
            key={item.title}
            className="landing-offer-item flex items-center gap-4 rounded-[1.5rem] bg-(--l-paper) p-3 pr-5"
          >
            <span className="grid size-16 shrink-0 place-items-center rounded-[1.1rem] bg-(--l-paper-deep)">
              <Glyph name={item.glyph} className="landing-glyph size-11" />
            </span>
            <span>
              <span className="block text-title">{item.title}</span>
              <span className="block text-small text-(--l-quiet)">
                {item.text}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Everything the app takes in and gives back, joined by threads that draw themselves as
 * the section scrolls by.
 */
export function Offer() {
  return (
    <section
      id="offer"
      data-tone="flax"
      className="relative overflow-hidden bg-(--l-flax) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto max-w-[90rem]">
        <Eyebrow number="02">What it does</Eyebrow>
        <div className="mt-8 grid gap-8 lg:grid-cols-[1.2fr_1fr] lg:items-end">
          <h2
            data-motion="lines"
            className="text-[clamp(2.75rem,6vw,6rem)] leading-[0.92] font-bold tracking-[-0.04em]"
          >
            <Lines
              lines={[
                "Every kind of money.",
                <span key="b" className="text-(--l-rust)">
                  One record.
                </span>,
              ]}
            />
          </h2>
          <p className="max-w-[46ch] text-lead">
            Not only M-Pesa. Salaries, client payments and the tax they
            withheld, bank alerts, receipts and cash. Each is read, sorted by
            what it was for, and kept next to its original.
          </p>
        </div>

        <ul className="mt-10 flex flex-wrap gap-2" aria-label="Who it is for">
          {AUDIENCE.map((who) => (
            <li
              key={who}
              className="rounded-full bg-(--l-ink) px-4 py-2 text-small text-(--l-paper)"
            >
              {who}
            </li>
          ))}
        </ul>

        <div className="mt-16 grid gap-10 lg:grid-cols-[1fr_minmax(8rem,14rem)_1fr] lg:gap-0">
          <Column heading="You send" items={SENDS} />
          <Threads from={SENDS.length} to={GETS.length} />
          <Column heading="You get" items={GETS} />
        </div>

        <MoneySplit />
      </div>
    </section>
  );
}

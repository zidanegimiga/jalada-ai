import { EVIDENCE } from "../../content";
import { Contours } from "../Contours";
import { HeroLedger } from "../HeroLedger";
import { RollLink } from "../RollLink";
import { Lines } from "../SplitText";

/**
 * The opening. Evidence of every kind floats around the promise; scrolling pulls it into
 * one ledger.
 */
export function Hero() {
  return (
    <section
      data-motion="gather depth"
      data-tone="light"
      data-cursor="Scroll"
      className="relative overflow-hidden bg-(--l-paper) text-(--l-ink)"
    >
      <Contours className="pointer-events-none absolute inset-0 size-full text-(--l-ink) opacity-[0.07]" />
      <div
        data-stage=""
        className="relative flex min-h-dvh flex-col items-center justify-center px-4 pt-28 pb-16 md:px-8"
      >
        {EVIDENCE.map((item) => (
          <div
            key={item.kind}
            data-chip=""
            className={`absolute hidden w-56 lg:block xl:w-64 ${item.place}`}
          >
            <div data-depth={item.depth}>
              <div
                data-pop=""
                className="rounded-[1.25rem] bg-(--l-card) p-4 shadow-[0_24px_48px_-24px_rgb(0_0_0/0.35)]"
              >
                <p className="font-mono text-[0.625rem] tracking-[0.16em] text-(--l-rust) uppercase">
                  {item.kind}
                </p>
                <p className="mt-2 text-small leading-snug">{item.body}</p>
              </div>
            </div>
          </div>
        ))}

        <div
          data-heading=""
          className="relative z-20 flex max-w-5xl flex-col items-center text-center"
        >
          <p
            data-intro=""
            className="font-mono text-tiny tracking-[0.2em] uppercase"
          >
            Money records for Kenya
          </p>
          <h1 className="mt-6 text-[clamp(3.25rem,10vw,9.5rem)] leading-[0.92] font-bold tracking-[-0.045em]">
            <Lines
              intro
              lines={[
                "Every shilling.",
                <>
                  On the <span className="text-(--l-rust)">record.</span>
                </>,
              ]}
            />
          </h1>
          <p
            data-intro=""
            className="mt-8 max-w-[44ch] text-lead text-(--l-quiet)"
          >
            For people with no accountant. Send an M-Pesa or bank message, a
            receipt, a payslip or a tax certificate. It is read, sorted by what
            it was for and kept with the original.
          </p>
          <div
            data-intro=""
            className="mt-10 flex flex-wrap items-center justify-center gap-3"
          >
            <RollLink href="/signup" size="lg">
              Start your records
            </RollLink>
            <RollLink href="#how" tone="line" size="lg">
              See how it works
            </RollLink>
          </div>
        </div>

        {/* On wide screens the ledger waits in the middle for the evidence to arrive. */}
        <div className="pointer-events-none mt-14 flex w-full justify-center md:motion-safe:absolute md:motion-safe:inset-0 md:motion-safe:mt-0 md:motion-safe:items-center">
          <div className="pointer-events-auto w-full max-w-[34rem]">
            <HeroLedger />
          </div>
        </div>

        <p
          data-intro=""
          data-cue=""
          className="absolute bottom-6 left-1/2 hidden -translate-x-1/2 items-center gap-3 font-mono text-tiny tracking-[0.2em] uppercase md:flex"
        >
          <span className="landing-scroll-cue" aria-hidden="true" />
          Scroll to gather
        </p>
      </div>
    </section>
  );
}

import Link from "next/link";

import { RollLink } from "../RollLink";
import { Lines } from "../SplitText";

/** The last ask, and the footer under it. */
export function Closing() {
  return (
    <>
      <section
        data-tone="pumpkin"
        data-cursor="Start"
        className="relative overflow-hidden bg-(--l-pumpkin) px-4 pt-32 pb-24 text-(--l-ink) md:px-8 md:pt-44 md:pb-32"
      >
        <div className="mx-auto flex max-w-[90rem] flex-col items-start gap-12 md:flex-row md:items-end md:justify-between">
          <h2
            data-motion="lines"
            className="text-[clamp(3.25rem,9vw,9rem)] leading-[0.9] font-bold tracking-[-0.05em]"
          >
            <Lines lines={["Start the", "record today."]} />
          </h2>
          <div className="flex flex-col items-start gap-4 md:items-end">
            <RollLink href="/signup" tone="ink" size="lg">
              Create an account
            </RollLink>
            <Link
              href="/signin"
              className="landing-underline min-h-tap text-body font-medium"
            >
              I already have one
            </Link>
          </div>
        </div>
      </section>

      <footer
        data-tone="dark"
        className="overflow-hidden bg-(--l-ink) px-4 pt-16 text-(--l-paper) md:px-8"
      >
        <div className="mx-auto flex max-w-[90rem] flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <p className="max-w-[36ch] text-body text-(--l-quiet-on-ink)">
            Money records for people in Kenya who don&apos;t have an accountant.
          </p>
          <nav aria-label="Footer" className="flex flex-wrap gap-x-6">
            <Link href="/signin" className="landing-underline min-h-tap">
              Sign in
            </Link>
            <Link href="/signup" className="landing-underline min-h-tap">
              Create an account
            </Link>
            <Link href="/privacy" className="landing-underline min-h-tap">
              Privacy notice
            </Link>
          </nav>
        </div>
        <p
          aria-hidden="true"
          data-motion="grow"
          className="mx-auto mt-10 max-w-[90rem] origin-bottom text-center text-[clamp(5rem,24vw,24rem)] leading-[0.78] font-bold tracking-[-0.06em] text-(--l-pumpkin)"
        >
          Jalada
        </p>
      </footer>
    </>
  );
}

import Link from "next/link";

import { CREDIT } from "../../site";
import { Contours } from "../Contours";
import { KikoiBand } from "../KikoiBand";
import { RollLink } from "../RollLink";
import { Lines } from "../SplitText";

const FOOTER_LINKS = [
  { label: "Sign in", href: "/signin" },
  { label: "Create an account", href: "/signup" },
  { label: "Privacy notice", href: "/privacy" },
];

/** The last ask, and the footer under it, with who made the app and where. */
export function Closing() {
  return (
    <>
      <section
        data-tone="pumpkin"
        data-cursor="Start"
        className="relative overflow-hidden bg-(--l-pumpkin) px-4 pt-32 pb-24 text-(--l-ink) md:px-8 md:pt-44 md:pb-32"
      >
        <Contours
          lines={18}
          className="pointer-events-none absolute inset-0 size-full text-(--l-ink) opacity-[0.12]"
        />
        <div className="relative mx-auto flex max-w-[90rem] flex-col items-start gap-12 md:flex-row md:items-end md:justify-between">
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

      <KikoiBand className="block bg-(--l-ink)" />

      <footer
        data-tone="dark"
        data-cursor="Asante"
        className="overflow-hidden bg-(--l-ink) px-4 pt-16 text-(--l-paper) md:px-8"
      >
        <div className="mx-auto grid max-w-[90rem] gap-10 md:grid-cols-[1fr_auto] md:items-start">
          <div>
            <p className="max-w-[36ch] text-body text-(--l-quiet-on-ink)">
              Money records for people in Kenya who don&apos;t have an
              accountant.
            </p>
            <p className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-1 text-body">
              <span>
                Built by{" "}
                <a
                  href={CREDIT.href}
                  className="font-medium text-(--l-pumpkin) underline-offset-4 hover:underline"
                >
                  {CREDIT.name}
                </a>
              </span>
              <span
                aria-hidden="true"
                className="size-1 rounded-full bg-current"
              />
              <span className="font-mono text-tiny tracking-[0.18em] uppercase">
                Made in Kenya
              </span>
            </p>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap gap-x-6">
            {FOOTER_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="landing-underline min-h-tap"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <p
          aria-hidden="true"
          data-motion="grow"
          data-ghost="Jalada"
          className="landing-ghost mx-auto mt-10 max-w-[90rem] origin-bottom text-center text-[clamp(5rem,24vw,24rem)] leading-[0.78] text-(--l-pumpkin)"
        />
      </footer>
    </>
  );
}

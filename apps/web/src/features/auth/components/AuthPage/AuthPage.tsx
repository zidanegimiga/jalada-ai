import { Suspense, type ReactNode } from "react";

import { GoogleOption } from "../GoogleOption";
import { HandoffLink } from "../Handoff";
import { JourneyPanel } from "../JourneyPanel";

const MODES = {
  signin: { tag: "Sign in", panel: "Back to your records." },
  signup: { tag: "New account", panel: "From message to tax return." },
} as const;

type AuthPageProps = {
  mode: keyof typeof MODES;
  /** The headline, with its last word in `emphasis`: "Welcome" + "back." */
  title: string;
  emphasis: string;
  intro: string;
  notice?: ReactNode;
  children: ReactNode;
  footer: {
    text: string;
    linkLabel: string;
    href: string;
    destination: string;
  };
};

/** Sign-in and sign-up: the form in a card, and the journey beside it on wide screens. */
export function AuthPage({
  mode,
  title,
  emphasis,
  intro,
  notice,
  children,
  footer,
}: AuthPageProps) {
  return (
    <main className="mx-auto grid w-full max-w-wide flex-1 gap-4 px-gutter pb-8 lg:grid-cols-[1.1fr_1fr] lg:gap-5">
      <section className="flex flex-col rounded-card border border-border bg-card motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-4 motion-safe:duration-700">
        <div className="flex items-center justify-between border-b border-dashed border-border px-card py-4 sm:px-10">
          <p className="font-mono text-tiny tracking-widest text-muted-foreground uppercase">
            Jalada AI
          </p>
          <p className="rounded-control bg-foreground px-2 py-1 font-mono text-tiny font-bold tracking-widest text-background uppercase">
            {MODES[mode].tag}
          </p>
        </div>
        <div className="flex flex-1 flex-col justify-center gap-7 px-card py-8 sm:px-10 sm:py-12">
          <div className="flex flex-col gap-3">
            <h1 className="text-display sm:text-hero">
              {title} <span className="text-(--emphasis)">{emphasis}</span>
            </h1>
            <p className="text-lead text-muted-foreground">{intro}</p>
          </div>
          {notice}
          <Suspense>
            <GoogleOption />
          </Suspense>
          {children}
        </div>
        <p className="flex flex-wrap items-center gap-x-2 border-t border-dashed border-border px-card py-3 sm:px-10">
          <span className="text-muted-foreground">{footer.text}</span>
          <HandoffLink
            href={footer.href}
            destination={footer.destination}
            className="inline-flex min-h-tap items-center font-medium underline decoration-(--emphasis) decoration-2 underline-offset-4"
          >
            {footer.linkLabel}
          </HandoffLink>
        </p>
      </section>
      <JourneyPanel heading={MODES[mode].panel} />
    </main>
  );
}

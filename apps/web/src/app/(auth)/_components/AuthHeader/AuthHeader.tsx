import Link from "next/link";

import { Brand } from "@/shared/components/Brand";
import { ThemeToggle } from "@/shared/components/ThemeToggle";

/** The bar above sign-in and sign-up: the brand, a word on privacy, and the theme. */
export function AuthHeader() {
  return (
    <header className="mx-auto flex w-full max-w-wide items-center gap-3 px-gutter pt-[calc(env(safe-area-inset-top)+1rem)] pb-4">
      <Link
        href="/signin"
        className="mr-auto flex min-h-tap items-center rounded-control"
      >
        <Brand />
      </Link>
      <Link
        href="/privacy"
        className="hidden min-h-tap items-center gap-2 rounded-full border border-border px-3 py-1.5 font-mono text-tiny tracking-wide text-muted-foreground uppercase transition-colors hover:border-foreground/40 hover:text-foreground sm:flex"
      >
        {/* <span
          aria-hidden="true"
          className="size-1.5 rounded-full bg-primary motion-safe:animate-pulse"
        /> */}
        Private · Encrypted
      </Link>
      <ThemeToggle />
    </header>
  );
}

import Link from "next/link";

import { buttonVariants } from "@/shared/components/Button";

/** Shown for an address that does not exist, or a record that is not yours. */
export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col justify-center gap-4 px-gutter py-8">
      <h1 className="text-display">Nothing here</h1>
      <p className="text-lead text-muted-foreground">
        This page does not exist, or it belongs to another account.
      </p>
      <Link href="/" className={buttonVariants({ size: "lg" })}>
        Go home
      </Link>
    </main>
  );
}

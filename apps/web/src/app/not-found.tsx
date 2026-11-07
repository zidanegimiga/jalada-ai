import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

/** Shown for an address that does not exist, or a record that is not yours. */
export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 px-4 py-8">
      <h1 className="text-3xl font-bold">Nothing here</h1>
      <p className="text-lg text-muted-foreground">
        This page does not exist, or it belongs to another account.
      </p>
      <Link href="/" className={buttonVariants({ size: "lg" })}>
        Go home
      </Link>
    </main>
  );
}

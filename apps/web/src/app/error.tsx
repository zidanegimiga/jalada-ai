"use client";

import * as Sentry from "@sentry/nextjs";
import Link from "next/link";
import { useEffect } from "react";

import { Button, buttonVariants } from "@/components/ui/button";

/**
 * Shown when a page fails to load or render. The error is reported, and the person can
 * try again or go home. The reference matches the error in the server's logs.
 */
export default function PageError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 px-4 py-8">
      <h1 className="text-3xl font-bold">Something went wrong</h1>
      <p className="text-lg text-muted-foreground">
        This page did not load. Your records are safe. If it keeps happening,
        the app may be waking up after a quiet spell: wait a moment and try
        again.
      </p>
      <Button size="lg" onClick={reset}>
        Try again
      </Button>
      <Link
        href="/"
        className={buttonVariants({ variant: "outline", size: "lg" })}
      >
        Go home
      </Link>
      {error.digest && (
        <p className="text-sm text-muted-foreground">
          Reference: <span className="font-mono">{error.digest}</span>
        </p>
      )}
    </main>
  );
}

"use client";

import * as Sentry from "@sentry/nextjs";
import Link from "next/link";
import { useEffect } from "react";

import "./globals.css";

/** Shown when the app itself fails to render. Reports the error, then offers a way back. */
export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center text-foreground">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-muted-foreground">
          It has been reported. Your records are safe.
        </p>
        <Link href="/" className="underline underline-offset-4">
          Back to Jalada AI
        </Link>
      </body>
    </html>
  );
}

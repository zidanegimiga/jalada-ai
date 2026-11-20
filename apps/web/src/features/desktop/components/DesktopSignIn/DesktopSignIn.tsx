"use client";

import { Laptop } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button, buttonVariants } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";

import { HandBack } from "../HandBack";

import { requestDesktopCode } from "../../api/desktop.api";
import { backToApp, type DesktopRequest } from "../../desktop-sign-in";

type Step = "asking" | "sending";

/**
 * Asks before signing the desktop app in as the person (decision 0029). Allowing it makes a
 * one-time code and opens the app with it; the code is useless without the app's secret.
 */
export function DesktopSignIn({ request }: { request: DesktopRequest | null }) {
  const [step, setStep] = useState<Step>("asking");
  const [error, setError] = useState<string | null>(null);
  // The link back to the app, once the person has allowed it.
  const [handBack, setHandBack] = useState<string | null>(null);

  if (!request) {
    return (
      <p className="text-muted-foreground">
        This link did not come from the Jalada AI desktop app. Open the app and
        choose Sign in there.
      </p>
    );
  }

  async function allow(desktop: DesktopRequest) {
    setStep("sending");
    setError(null);
    try {
      const code = await requestDesktopCode(desktop.challenge);
      const link = backToApp(code, desktop.state);
      setHandBack(link);
      window.location.href = link;
    } catch {
      setError("That did not work. Go back to the app and try again.");
      setStep("asking");
    }
  }

  if (handBack) return <HandBack link={handBack} />;

  return (
    <section className="flex flex-col gap-4 rounded-card bg-card p-card">
      <span className="grid size-14 place-items-center rounded-card bg-secondary text-secondary-foreground">
        <Laptop aria-hidden="true" className="size-icon-lg" />
      </span>
      <p className="text-lead">
        The Jalada AI desktop app on this computer wants to sign in as you. It
        keeps an encrypted copy of your records on this computer, so you can use
        them offline.
      </p>
      <p className="text-muted-foreground">
        Only allow this if you just chose Sign in in the desktop app.
      </p>
      <FormError message={error} />
      <div className="flex flex-wrap gap-3">
        <Button
          size="lg"
          onClick={() => void allow(request)}
          disabled={step === "sending"}
        >
          Allow
        </Button>
        <Link
          href="/"
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          Not now
        </Link>
      </div>
    </section>
  );
}

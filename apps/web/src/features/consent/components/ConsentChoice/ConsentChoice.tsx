"use client";

import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useSyncExternalStore } from "react";

import { Button } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";
import { cn } from "@/shared/styles/cn";

import { setModelConsent, type ModelConsent } from "../../api/consent.api";

const LATER = "jalada:consent-later";

type Place = "home" | "account" | "ask";

type ConsentChoiceProps = {
  consent: ModelConsent;
  /** Home asks once and can be put off; Account changes it; Ask needs it to go on. */
  place: Place;
};

const SAY = {
  home: "Read blurry photos and answer your questions?",
  account: "Reading with AI",
  ask: "Allow reading with AI to ask about your records",
} satisfies Record<Place, string>;

function subscribe() {
  return () => {};
}

function putOff(): boolean {
  try {
    return window.localStorage.getItem(LATER) === "yes";
  } catch {
    return false;
  }
}

/**
 * The question decision 0026 asks before a model reads anyone's records: who reads them, that
 * it is outside Kenya, and what happens without it. The answer is kept by the API and can be
 * changed on the Account page at any time.
 */
export function ConsentChoice({ consent, place }: ConsentChoiceProps) {
  const router = useRouter();
  const [given, setGiven] = useState(consent.given);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const later = useSyncExternalStore(subscribe, putOff, () => false);
  const [hidden, setHidden] = useState(false);

  if (!consent.required) return null;
  if (place === "home" && (given || later || hidden)) return null;

  async function answer(agree: boolean) {
    setBusy(true);
    setError(null);
    try {
      setGiven((await setModelConsent(agree)).given);
      router.refresh();
    } catch (problem) {
      setError(
        problem instanceof Error ? problem.message : "That did not save.",
      );
    } finally {
      setBusy(false);
    }
  }

  function notNow() {
    try {
      window.localStorage.setItem(LATER, "yes");
    } catch {
      // Without storage it simply asks again next time.
    }
    setHidden(true);
  }

  const headingId = `consent-${place}`;
  return (
    <section
      aria-labelledby={headingId}
      className={cn(
        "flex flex-col gap-4 rounded-card border bg-card p-card",
        place === "account" ? "border-border" : "border-primary/40",
        place !== "account" &&
          "motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:duration-500",
      )}
    >
      <h2 id={headingId} className="flex items-center gap-2 text-title">
        <ShieldCheck aria-hidden="true" className="size-icon shrink-0" />
        {SAY[place]}
      </h2>
      <div className="flex flex-col gap-2 text-muted-foreground">
        <p>
          To read photos the app cannot read on its own, and to answer your
          questions, Jalada AI sends your receipts, M-Pesa messages and
          questions to a language model provider outside Kenya:
        </p>
        <p className="rounded-control bg-muted px-4 py-3 text-foreground">
          {consent.notice}
        </p>
        <p>
          Without this, photos are read on Jalada AI&apos;s side only, and Ask
          is off. You can change this at any time on your Account page. The{" "}
          <Link href="/privacy" className="underline underline-offset-4">
            privacy notice
          </Link>{" "}
          lists everywhere your data goes.
        </p>
      </div>
      {place === "account" && given ? (
        <div className="flex flex-wrap items-center gap-3">
          <p className="flex-1 font-medium">Allowed.</p>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => void answer(false)}
          >
            Stop reading with AI
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          <Button disabled={busy} onClick={() => void answer(true)}>
            Allow
          </Button>
          {place === "home" && (
            <Button variant="outline" disabled={busy} onClick={notNow}>
              Not now
            </Button>
          )}
        </div>
      )}
      <FormError message={error} />
    </section>
  );
}

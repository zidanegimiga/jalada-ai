"use client";

import { Check, Download, Share } from "lucide-react";
import { useSyncExternalStore } from "react";

import { Button } from "@/shared/components/Button";

import {
  askToInstall,
  installState,
  subscribe,
  type InstallState,
} from "../../install-prompt";

/** What each state says, under the heading. */
const MESSAGES: Record<InstallState, string> = {
  installed: "Jalada AI is installed on this device.",
  ready:
    "Open Jalada AI from your home screen or dock, in its own window, and start faster.",
  ios: "In Safari, tap Share, then Add to Home Screen.",
  unavailable:
    "Open this page in Chrome, Edge, Samsung Internet or Safari to install it.",
};

/** Installing the web app on this phone or computer (decision 0028). */
export function InstallCard() {
  const state = useSyncExternalStore(
    subscribe,
    installState,
    (): InstallState => "unavailable",
  );
  return (
    <section
      aria-labelledby="install-heading"
      className="flex flex-col gap-3 rounded-card border border-border bg-card p-card"
    >
      <h2 id="install-heading" className="text-title">
        Install the app
      </h2>
      <p className="flex items-start gap-2 text-muted-foreground">
        {state === "installed" && (
          <Check
            aria-hidden="true"
            className="mt-0.5 size-icon shrink-0 text-money-in"
          />
        )}
        {state === "ios" && (
          <Share aria-hidden="true" className="mt-0.5 size-icon shrink-0" />
        )}
        {MESSAGES[state]}
      </p>
      {state === "ready" && (
        <Button size="lg" onClick={() => void askToInstall()}>
          <Download aria-hidden="true" />
          Install Jalada AI
        </Button>
      )}
    </section>
  );
}

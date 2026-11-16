"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

import { sayOwnAccount } from "../api";

const WORDING = {
  out: "Is this your own account? Money you move to your own bank or savings is not spending.",
  in: "Did this come from your own account? Money you move from your own bank or savings is not income.",
};

/** For money to or from a bank or savings account: money moved between the user's own
 * accounts is a transfer. A "no" needs no button: choosing a category answers it. */
export function OwnAccountQuestion({
  entryId,
  direction,
}: {
  entryId: string;
  direction: "in" | "out";
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function yes() {
    setError(null);
    try {
      await sayOwnAccount(entryId);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-inset border border-border px-4 py-3">
      <p>{WORDING[direction]} If it is not yours, choose what it was for.</p>
      <Button variant="outline" onClick={yes} className="self-start">
        Yes, it is my account
      </Button>
      <FormError message={error} />
    </div>
  );
}

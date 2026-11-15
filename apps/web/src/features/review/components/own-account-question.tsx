"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { sayOwnAccount } from "../api";

/** For a payment to a bank or savings paybill: money moved to the user's own account is
 * a transfer, not spending. A "no" needs no button: choosing a category answers it. */
export function OwnAccountQuestion({ entryId }: { entryId: string }) {
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
    <div className="flex flex-col gap-2 rounded-2xl border border-border px-4 py-3">
      <p>
        Is this your own account? Money you move to your own bank or savings is
        not spending. If it is not yours, choose what it was for.
      </p>
      <Button variant="outline" onClick={yes} className="self-start">
        Yes, it is my account
      </Button>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

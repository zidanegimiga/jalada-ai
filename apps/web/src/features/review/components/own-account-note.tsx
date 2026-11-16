"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

import { takeBackOwnAccount } from "../api";

/** A transfer to or from an account the user said is theirs, with a way to take that
 * back. Undo makes it a payment again, with what it was for still to choose. */
export function OwnAccountNote({
  entryId,
  account,
  direction,
}: {
  entryId: string;
  account: string;
  direction: "in" | "out";
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function undo() {
    setError(null);
    try {
      await takeBackOwnAccount(entryId);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-inset border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <p>
          {direction === "in" ? "From" : "To"} your own account, {account}.
        </p>
        <Button variant="ghost" onClick={undo}>
          Undo
        </Button>
      </div>
      <FormError message={error} />
    </div>
  );
}

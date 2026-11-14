"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

/** For evidence that does not record money moving, such as a balance message. Asks once
 * before removing it, since it then leaves the list. */
export function NotATransaction({ onConfirm }: { onConfirm: () => void }) {
  const [asking, setAsking] = useState(false);

  if (!asking) {
    return (
      <Button variant="ghost" onClick={() => setAsking(true)}>
        Not a transaction
      </Button>
    );
  }
  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-secondary p-4 text-secondary-foreground">
      <p>
        This will not be counted anywhere. The original stays in your records.
      </p>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" onClick={() => setAsking(false)}>
          Keep it
        </Button>
        <Button onClick={onConfirm}>Not a transaction</Button>
      </div>
    </div>
  );
}

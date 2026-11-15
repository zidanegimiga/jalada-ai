"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { putBack } from "../api";

/** For evidence marked "Not a transaction" by mistake: puts it back on To check. */
export function PutBack({ id }: { id: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setError(null);
    try {
      await putBack(id);
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={onClick}
        className="underline underline-offset-4"
      >
        Put back
      </button>
      {error && (
        <span role="alert" className="text-destructive">
          {error}
        </span>
      )}
    </>
  );
}

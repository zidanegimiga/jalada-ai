"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { FormError } from "@/shared/components/FormError";

import { putBack } from "../../api/evidence.api";

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
        className="inline-flex min-h-tap items-center underline underline-offset-4"
      >
        Put back
      </button>
      <FormError message={error} />
    </>
  );
}

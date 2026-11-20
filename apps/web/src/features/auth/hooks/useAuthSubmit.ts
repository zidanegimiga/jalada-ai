"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { RETURN_PARAM, safeReturnPath } from "@/shared/config/return-path";

import { AuthError } from "../api/auth.api";

/**
 * Runs a sign-in or sign-up call, shows its error, and when it succeeds goes back to the
 * page that sent the person here, or home.
 */
export function useAuthSubmit(action: (form: FormData) => Promise<unknown>) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await action(new FormData(event.currentTarget));
      const next = new URLSearchParams(window.location.search).get(
        RETURN_PARAM,
      );
      router.replace(safeReturnPath(next));
      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof AuthError
          ? caught.message
          : "Something went wrong. Try again.",
      );
      setPending(false);
    }
  }

  return { error, pending, onSubmit };
}

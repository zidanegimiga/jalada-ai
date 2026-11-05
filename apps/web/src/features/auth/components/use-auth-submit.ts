"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthError } from "../api";

/** Runs a sign-in or sign-up call, shows its error, and goes home when it succeeds. */
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
      router.replace("/");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof AuthError ? caught.message : "Something went wrong. Try again.");
      setPending(false);
    }
  }

  return { error, pending, onSubmit };
}

"use client";

import { Button } from "@/shared/components/Button";
import { FormError } from "@/shared/components/FormError";

import { signIn } from "../../api/auth.api";
import { FormField } from "../FormField";
import { useAuthSubmit } from "../../hooks/useAuthSubmit";

export function SignInForm() {
  const { error, pending, onSubmit } = useAuthSubmit((form) =>
    signIn(String(form.get("email")), String(form.get("password"))),
  );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <FormField label="Email" name="email" type="email" autoComplete="email" />
      <FormField label="Password" name="password" type="password" autoComplete="current-password" />
      <FormError message={error} />
      <Button type="submit" size="lg" disabled={pending}>
        {pending ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}

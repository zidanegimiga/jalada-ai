"use client";

import { ActionButton } from "@/shared/components/ActionButton";
import { FormError } from "@/shared/components/FormError";

import { signIn } from "../../api/auth.api";
import { useAuthSubmit } from "../../hooks/useAuthSubmit";
import { AuthField } from "../AuthField";

export function SignInForm() {
  const { error, pending, onSubmit } = useAuthSubmit((form) =>
    signIn(String(form.get("email")), String(form.get("password"))),
  );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-6">
      <AuthField
        number="01"
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        placeholder="you@example.com"
      />
      <AuthField
        number="02"
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        placeholder="Your password"
      />
      <FormError message={error} />
      <ActionButton type="submit" busy={pending}>
        {pending ? "Signing in..." : "Sign in"}
      </ActionButton>
    </form>
  );
}

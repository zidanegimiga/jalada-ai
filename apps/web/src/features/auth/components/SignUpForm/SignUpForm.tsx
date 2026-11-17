"use client";

import { ActionButton } from "@/shared/components/ActionButton";
import { FormError } from "@/shared/components/FormError";

import { signUp } from "../../api/auth.api";
import { useAuthSubmit } from "../../hooks/useAuthSubmit";
import { AuthField } from "../AuthField";

export function SignUpForm() {
  const { error, pending, onSubmit } = useAuthSubmit((form) =>
    signUp(
      String(form.get("email")),
      String(form.get("password")),
      String(form.get("name")),
    ),
  );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-6">
      <AuthField
        number="01"
        label="Your name"
        name="name"
        autoComplete="name"
        maxLength={80}
        placeholder="Wanjiru Kamau"
      />
      <AuthField
        number="02"
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        placeholder="you@example.com"
      />
      <AuthField
        number="03"
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        minLength={10}
        maxLength={128}
        placeholder="Choose a password"
        hint="At least 10 characters."
      />
      <FormError message={error} />
      <ActionButton type="submit" busy={pending}>
        {pending ? "Creating account..." : "Create account"}
      </ActionButton>
    </form>
  );
}

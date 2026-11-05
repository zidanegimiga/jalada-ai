"use client";

import { Button } from "@/components/ui/button";

import { signIn } from "../api";
import { FormField } from "./form-field";
import { useAuthSubmit } from "./use-auth-submit";

export function SignInForm() {
  const { error, pending, onSubmit } = useAuthSubmit((form) =>
    signIn(String(form.get("email")), String(form.get("password"))),
  );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <FormField label="Email" name="email" type="email" autoComplete="email" />
      <FormField label="Password" name="password" type="password" autoComplete="current-password" />
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" disabled={pending}>
        {pending ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}

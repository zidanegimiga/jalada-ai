"use client";

import { Button } from "@/components/ui/button";

import { signUp } from "../api";
import { FormField } from "./form-field";
import { useAuthSubmit } from "./use-auth-submit";

export function SignUpForm() {
  const { error, pending, onSubmit } = useAuthSubmit((form) =>
    signUp(String(form.get("email")), String(form.get("password")), String(form.get("name"))),
  );

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <FormField label="Your name" name="name" autoComplete="name" maxLength={80} />
      <FormField label="Email" name="email" type="email" autoComplete="email" />
      <FormField
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        minLength={10}
        maxLength={128}
        aria-describedby="password-hint"
      />
      <p id="password-hint" className="-mt-3 text-sm text-muted-foreground">
        At least 10 characters.
      </p>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" disabled={pending}>
        {pending ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}

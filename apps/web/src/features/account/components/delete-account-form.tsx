"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/** Deleting cannot be undone, so the email has to be typed out before the button works. */
export function DeleteAccountForm({ email }: { email: string }) {
  const router = useRouter();
  const id = useId();
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const matches = typed.trim().toLowerCase() === email.toLowerCase();

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const response = await fetch("/v1/account", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: typed }),
    });
    if (response.ok) {
      router.replace("/signup");
      router.refresh();
      return;
    }
    const data = await response.json().catch(() => ({}));
    setError(data.error?.message ?? "That did not work. Try again.");
    setBusy(false);
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <Label htmlFor={id}>Type {email} to confirm</Label>
      <Input
        id={id}
        value={typed}
        onChange={(event) => setTyped(event.target.value)}
        autoComplete="off"
      />
      <Button
        type="submit"
        variant="destructive"
        size="lg"
        disabled={!matches || busy}
      >
        {busy ? "Deleting..." : "Delete my account"}
      </Button>
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </form>
  );
}

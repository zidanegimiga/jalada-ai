"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

import { signOut } from "../api";

export function SignOutButton() {
  const router = useRouter();

  async function onClick() {
    await signOut();
    router.replace("/signin");
    router.refresh();
  }

  return (
    <Button variant="outline" size="sm" onClick={onClick}>
      Sign out
    </Button>
  );
}

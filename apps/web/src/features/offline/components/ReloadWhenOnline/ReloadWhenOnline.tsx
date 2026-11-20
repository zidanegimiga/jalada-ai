"use client";

import { RotateCw } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/shared/components/Button";

import { useOnline } from "../../hooks/useOnline";

/**
 * Reloads the page the person was trying to open once the connection returns, and offers a
 * button to try sooner. The offline page is shown at that page's own address, so a reload
 * is all it takes.
 */
export function ReloadWhenOnline() {
  const online = useOnline();

  useEffect(() => {
    const reload = () => window.location.reload();
    window.addEventListener("online", reload);
    return () => window.removeEventListener("online", reload);
  }, []);

  return (
    <Button
      size="lg"
      variant="secondary"
      onClick={() => window.location.reload()}
    >
      <RotateCw aria-hidden="true" />
      {online ? "Try again" : "Waiting for a connection"}
    </Button>
  );
}

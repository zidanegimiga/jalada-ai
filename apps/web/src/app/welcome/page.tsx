import type { Metadata } from "next";

import { Landing } from "@/features/landing";

export const metadata: Metadata = {
  title: "Jalada AI: every shilling, on the record",
  description:
    "Send a receipt photo, a PDF or an M-Pesa message. Jalada AI reads it, sorts it and keeps it next to the original, so filing time is boring.",
};

/** Shown at / to visitors who are not signed in (see proxy.ts). */
export default function WelcomePage() {
  return <Landing />;
}

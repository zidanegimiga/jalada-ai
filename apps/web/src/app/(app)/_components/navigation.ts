import { BookOpen, Home, ListChecks, type LucideIcon } from "lucide-react";

export type Destination = { href: string; label: string; Icon: LucideIcon };

/** Where the main navigation goes, in order. Both the bottom bar and the side rail use it. */
export const DESTINATIONS: Destination[] = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/review", label: "To check", Icon: ListChecks },
  { href: "/ledger", label: "Ledger", Icon: BookOpen },
];

/** Which destination a path belongs to: /ledger/certificates/1 is still the ledger. */
export function currentIndex(pathname: string): number {
  return DESTINATIONS.findIndex(({ href }) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href),
  );
}

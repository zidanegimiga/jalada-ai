import {
  BookOpen,
  Home,
  ListChecks,
  MessageCircle,
  type LucideIcon,
} from "lucide-react";

export type Destination = { href: string; label: string; Icon: LucideIcon };

const ASK: Destination = { href: "/ask", label: "Ask", Icon: MessageCircle };

/** The places, with Ask only where the assistant is switched on (ASSISTANT=on at build). */
export function destinations(assistant: string | undefined): Destination[] {
  return [
    { href: "/", label: "Home", Icon: Home },
    { href: "/review", label: "To check", Icon: ListChecks },
    { href: "/ledger", label: "Ledger", Icon: BookOpen },
    ...(assistant === "on" ? [ASK] : []),
  ];
}

/** Where the main navigation goes, in order. Both the bottom bar and the side rail use it. */
export const DESTINATIONS: Destination[] = destinations(process.env.ASSISTANT);

/** Which destination a path belongs to: /ledger/certificates/1 is still the ledger. */
export function currentIndex(
  pathname: string,
  places: Destination[] = DESTINATIONS,
): number {
  return places.findIndex(({ href }) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href),
  );
}

"use client";

import { BookOpen, Home, ListChecks } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home", Icon: Home },
  { href: "/review", label: "To check", Icon: ListChecks },
  { href: "/ledger", label: "Ledger", Icon: BookOpen },
];

/** Bottom navigation, within reach of a thumb on a small phone. */
export function AppNav() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 border-t border-border bg-background pb-[env(safe-area-inset-bottom)]"
    >
      <ul className="mx-auto grid max-w-md grid-cols-3">
        {LINKS.map(({ href, label, Icon }) => {
          const current = pathname === href;
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={current ? "page" : undefined}
                className={`flex h-16 flex-col items-center justify-center gap-1 text-sm ${current ? "font-bold text-foreground" : "text-muted-foreground"}`}
              >
                <Icon
                  aria-hidden="true"
                  className={current ? "size-6 text-primary" : "size-6"}
                />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

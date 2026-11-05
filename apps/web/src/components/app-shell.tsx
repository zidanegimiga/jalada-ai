import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

import { AppNav } from "./app-nav";

/** The frame around every signed-in screen: name, account link, and the bottom navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 pt-8 pb-28">
        <header className="flex items-center justify-between">
          <p className="text-lg font-bold">Jalada AI</p>
          <Link
            href="/account"
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            Account
          </Link>
        </header>
        {children}
      </main>
      <AppNav />
    </>
  );
}

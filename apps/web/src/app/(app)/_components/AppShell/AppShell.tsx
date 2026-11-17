import Link from "next/link";

import { buttonVariants } from "@/shared/components/Button";

import { AppNav } from "../AppNav";
import { Brand } from "@/shared/components/Brand";

/** The frame around every signed-in screen: name, account link, and the bottom navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <main className="mx-auto flex w-full max-w-page flex-1 flex-col gap-section px-gutter pt-8 pb-28">
        <header className="flex items-center justify-between">
          <Brand />
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

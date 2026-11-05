import { SignOutButton } from "@/features/auth/components/sign-out-button";

import { AppNav } from "./app-nav";

/** The frame around every signed-in screen: name, sign out, and the bottom navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 pt-8 pb-28">
        <header className="flex items-center justify-between">
          <p className="text-lg font-bold">Jalada AI</p>
          <SignOutButton />
        </header>
        {children}
      </main>
      <AppNav />
    </>
  );
}

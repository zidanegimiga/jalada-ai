import { AppNav } from "../AppNav";
import { AppHeader } from "../AppHeader";

/** The frame around every signed-in screen: the top bar, the page, and the navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-page flex-1 flex-col gap-section px-gutter pt-6 pb-32">
        {children}
      </main>
      <AppNav />
    </>
  );
}

import { Suspense } from "react";

import { Skeleton } from "@/shared/components/Skeleton";

import { AppHeader } from "../AppHeader";
import { AppNav } from "../AppNav";
import { PageTransition } from "../PageTransition";
import { SideNav } from "../SideNav";
import { ToCheckBadge } from "../ToCheckBadge";
import { UserAvatar } from "../UserAvatar";

function toCheckBadge() {
  return (
    <Suspense>
      <ToCheckBadge />
    </Suspense>
  );
}

/**
 * The frame around every signed-in screen. On phones: the top bar, the page and the floating
 * bar. On wide screens: a rail down the left and a wider page.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col lg:grid lg:grid-cols-[15rem_1fr]">
      <SideNav
        toCheck={toCheckBadge()}
        account={
          <Suspense fallback={<Skeleton className="size-tap rounded-full" />}>
            <UserAvatar />
          </Suspense>
        }
      />
      <div className="flex flex-1 flex-col">
        <AppHeader />
        <main className="mx-auto flex w-full max-w-page flex-1 flex-col px-gutter pt-6 pb-32 lg:max-w-content lg:pt-10 lg:pb-16">
          <PageTransition>
            <div className="flex flex-col gap-section">{children}</div>
          </PageTransition>
        </main>
      </div>
      <AppNav toCheck={toCheckBadge()} />
    </div>
  );
}

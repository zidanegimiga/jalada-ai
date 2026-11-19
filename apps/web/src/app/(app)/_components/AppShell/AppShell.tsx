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
 * bar, and the whole window scrolls. On wide screens: a rail down the left that stays put,
 * and a page that scrolls on its own beside it, under its sticky header.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col lg:grid lg:h-dvh lg:grid-cols-[15rem_1fr] lg:overflow-hidden">
      <SideNav
        toCheck={toCheckBadge()}
        account={
          <Suspense fallback={<Skeleton className="size-tap rounded-full" />}>
            <UserAvatar />
          </Suspense>
        }
      />
      <div
        id="page-scroll"
        className="flex flex-1 flex-col lg:h-dvh lg:overflow-y-auto lg:overscroll-contain"
      >
        <AppHeader />
        <main className="mx-auto flex w-full max-w-page flex-1 flex-col px-gutter pt-6 pb-32 lg:max-w-content lg:pt-0 lg:pb-16 xl:max-w-wide">
          <PageTransition>
            <div className="flex flex-col gap-section">{children}</div>
          </PageTransition>
        </main>
      </div>
      <AppNav toCheck={toCheckBadge()} />
    </div>
  );
}

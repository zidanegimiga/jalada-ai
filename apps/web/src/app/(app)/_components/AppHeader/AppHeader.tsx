import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";

import { Skeleton } from "@/shared/components/Skeleton";
import { ThemeToggle } from "@/shared/components/ThemeToggle";

import { UserAvatar } from "../UserAvatar";

/** The bar at the top of every signed-in page: the logo, the theme and the account. */
export function AppHeader() {
  return (
    <header
      className="sticky top-0 z-40 border-b border-border bg-background pt-[env(safe-area-inset-top)] lg:hidden"
      // Its own layer in page transitions, so pages slide under it.
      style={{ viewTransitionName: "app-header" }}
    >
      <div className="mx-auto flex h-16 w-full max-w-page items-center gap-2 px-gutter">
        <Link
          href="/"
          aria-label="Jalada AI, home"
          className="mr-auto rounded-control transition-transform active:scale-95"
        >
          <Image
            src="/mark.webp"
            alt=""
            width={44}
            height={44}
            unoptimized
            priority
            className="size-tap rounded-control"
          />
        </Link>
        <ThemeToggle />
        <Suspense fallback={<Skeleton className="size-tap rounded-full" />}>
          <UserAvatar />
        </Suspense>
      </div>
    </header>
  );
}

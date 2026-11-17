import { Download } from "lucide-react";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { DeleteAccountForm } from "@/features/account/components/DeleteAccountForm";
import { Preferences } from "@/features/account/components/Preferences";
import { SignOutButton } from "@/features/auth/components/SignOutButton";
import { getCurrentUser } from "@/features/auth/server/get-current-user";
import {
  TelegramCard,
  TelegramCardSkeleton,
} from "@/features/telegram/components/TelegramCard";
import { getTelegramStatus } from "@/features/telegram/server/get-telegram-status";
import { Avatar } from "@/shared/components/Avatar";
import { buttonVariants } from "@/shared/components/Button";
import { Skeleton, SkeletonText } from "@/shared/components/Skeleton";

const IDENTITY =
  "flex items-center gap-4 rounded-card border border-border bg-card p-card";

async function Identity() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return (
    <section aria-label="You" className={IDENTITY}>
      <Avatar name={user.display_name} className="size-14 text-lead" />
      <div className="flex min-w-0 flex-1 flex-col">
        <p className="truncate text-lead font-medium">{user.display_name}</p>
        <p className="truncate text-muted-foreground">{user.email}</p>
      </div>
    </section>
  );
}

function IdentitySkeleton() {
  return (
    <section aria-label="You" aria-busy="true" className={IDENTITY}>
      <Skeleton className="size-14 shrink-0 rounded-full" />
      <div className="flex min-w-0 flex-1 flex-col">
        <p className="text-lead">
          <SkeletonText className="w-36" />
        </p>
        <p>
          <SkeletonText className="w-48" />
        </p>
      </div>
    </section>
  );
}

async function DeleteAccount() {
  const user = await getCurrentUser();
  return user ? <DeleteAccountForm email={user.email} /> : null;
}

async function Telegram() {
  const status = await getTelegramStatus();
  return <TelegramCard available={status.available} linked={status.linked} />;
}

export default function AccountPage() {
  return (
    <>
      <h1 className="text-display">Account</h1>
      <Suspense fallback={<IdentitySkeleton />}>
        <Identity />
      </Suspense>
      <Preferences />
      <Suspense fallback={<TelegramCardSkeleton />}>
        <Telegram />
      </Suspense>
      <section
        aria-labelledby="data-heading"
        className="flex flex-col gap-3 rounded-card border border-border bg-card p-card"
      >
        <h2 id="data-heading" className="text-title">
          Your data
        </h2>
        <p className="text-muted-foreground">
          Everything Jalada AI holds about you, with every receipt and message
          you sent, in one zip file.
        </p>
        <a
          href="/v1/account/export"
          download
          className={buttonVariants({ variant: "secondary", size: "lg" })}
        >
          <Download aria-hidden="true" />
          Download my data
        </a>
      </section>
      <SignOutButton />
      <section
        aria-labelledby="delete-heading"
        className="flex flex-col gap-3 rounded-card border border-destructive/40 bg-card p-card"
      >
        <h2 id="delete-heading" className="text-title">
          Delete my account
        </h2>
        <p className="text-muted-foreground">
          This deletes your account, your ledger and every receipt and message
          you sent. It cannot be undone. Download your data first if you want a
          copy.
        </p>
        <Suspense fallback={<Skeleton className="h-40" />}>
          <DeleteAccount />
        </Suspense>
      </section>
    </>
  );
}

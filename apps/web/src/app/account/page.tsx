import { Download } from "lucide-react";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { Spinner } from "@/components/ui/spinner";
import { buttonVariants } from "@/components/ui/button";
import { DeleteAccountForm } from "@/features/account/components/delete-account-form";
import { SignOutButton } from "@/features/auth/components/sign-out-button";
import { getVersions } from "@/features/account/server/get-versions";
import { getCurrentUser } from "@/features/auth/server/get-current-user";

async function Account() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return (
    <>
      <section className="flex flex-col gap-1">
        <p className="text-lg font-medium">{user.display_name}</p>
        <p className="text-muted-foreground">{user.email}</p>
      </section>
      <section
        aria-labelledby="data-heading"
        className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-5"
      >
        <h2 id="data-heading" className="text-xl font-bold">
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
      <section
        aria-labelledby="delete-heading"
        className="flex flex-col gap-3 rounded-3xl border border-destructive/40 bg-card p-5"
      >
        <h2 id="delete-heading" className="text-xl font-bold">
          Delete my account
        </h2>
        <p className="text-muted-foreground">
          This deletes your account, your ledger and every receipt and message
          you sent. It cannot be undone. Download your data first if you want a
          copy.
        </p>
        <DeleteAccountForm email={user.email} />
      </section>
      <SignOutButton />
    </>
  );
}

async function Versions() {
  const { web, api } = await getVersions();
  return (
    <p className="text-sm text-muted-foreground">
      Version: web {web}, API {api}
    </p>
  );
}

export default function AccountPage() {
  return (
    <AppShell>
      <h1 className="text-4xl font-bold">Account</h1>
      <Suspense fallback={<Spinner />}>
        <Account />
      </Suspense>
      <Suspense>
        <Versions />
      </Suspense>
    </AppShell>
  );
}

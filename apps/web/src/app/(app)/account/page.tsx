import { Download } from "lucide-react";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { Spinner } from "@/shared/components/Spinner";
import { buttonVariants } from "@/shared/components/Button";
import { DeleteAccountForm } from "@/features/account/components/DeleteAccountForm";
import { SignOutButton } from "@/features/auth/components/SignOutButton";
import { getVersions } from "@/features/account/server/get-versions";
import { getCurrentUser } from "@/features/auth/server/get-current-user";

async function Account() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return (
    <>
      <section className="flex flex-col gap-1">
        <p className="text-lead font-medium">{user.display_name}</p>
        <p className="text-muted-foreground">{user.email}</p>
      </section>
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
        <DeleteAccountForm email={user.email} />
      </section>
      <SignOutButton />
    </>
  );
}

async function Versions() {
  const { web, api } = await getVersions();
  return (
    <p className="text-small text-muted-foreground">
      Version: web {web}, API {api}
    </p>
  );
}

export default function AccountPage() {
  return (
    <>
      <h1 className="text-display">Account</h1>
      <Suspense fallback={<Spinner />}>
        <Account />
      </Suspense>
      <Suspense>
        <Versions />
      </Suspense>
    </>
  );
}

import { redirect } from "next/navigation";
import { Suspense } from "react";

import { SignOutButton } from "@/features/auth/components/sign-out-button";
import { getCurrentUser } from "@/features/auth/server/get-current-user";
import { CapturePanel } from "@/features/evidence/components/capture-panel";
import { EvidenceList } from "@/features/evidence/components/evidence-list";
import { getRecentEvidence } from "@/features/evidence/server/get-recent-evidence";

async function Greeting() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return <h1 className="text-4xl font-bold">Hello, {user.display_name}</h1>;
}

async function RecentEvidence() {
  return <EvidenceList items={await getRecentEvidence()} />;
}

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between">
        <p className="text-lg font-bold">Jalada AI</p>
        <SignOutButton />
      </header>
      <Suspense fallback={<div className="h-10" />}>
        <Greeting />
      </Suspense>
      <CapturePanel />
      <section aria-labelledby="recent-heading" className="flex flex-col gap-3">
        <h2 id="recent-heading" className="text-xl font-bold">
          Recent
        </h2>
        <Suspense
          fallback={<p className="text-muted-foreground">Loading...</p>}
        >
          <RecentEvidence />
        </Suspense>
      </section>
    </main>
  );
}

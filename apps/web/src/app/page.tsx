import { redirect } from "next/navigation";
import { Suspense } from "react";

import { SignOutButton } from "@/features/auth/components/sign-out-button";
import { getCurrentUser } from "@/features/auth/server/get-current-user";

async function Greeting() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  return <h1 className="text-4xl font-bold">Hello, {user.display_name}</h1>;
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
    </main>
  );
}

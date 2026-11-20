import type { Metadata } from "next";

import { DesktopSignIn } from "@/features/desktop/components/DesktopSignIn";
import { readDesktopRequest } from "@/features/desktop/desktop-sign-in";

import { PageHeader } from "../../_components/PageHeader";

export const metadata: Metadata = { title: "Sign in on the desktop app" };

/** Opened by the desktop app in the browser, where the person is already signed in. */
export default async function DesktopSignInPage({
  searchParams,
}: PageProps<"/desktop/sign-in">) {
  const request = readDesktopRequest(await searchParams);
  return (
    <div className="mx-auto flex w-full max-w-content flex-col gap-section">
      <PageHeader title="Sign in on this computer" />
      <DesktopSignIn request={request} />
    </div>
  );
}

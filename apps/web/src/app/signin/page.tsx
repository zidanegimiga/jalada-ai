import { Suspense } from "react";

import { AuthPage } from "@/features/auth/components/auth-page";
import { SignInForm } from "@/features/auth/components/sign-in-form";
import { SignInNotice } from "@/features/auth/components/sign-in-notice";

export default function SignInPage() {
  return (
    <AuthPage
      title="Welcome back"
      notice={
        <Suspense>
          <SignInNotice />
        </Suspense>
      }
      footer={{
        text: "New here?",
        linkLabel: "Create an account",
        href: "/signup",
      }}
    >
      <SignInForm />
    </AuthPage>
  );
}

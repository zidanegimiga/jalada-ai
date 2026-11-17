import { Suspense } from "react";

import { AuthPage } from "@/features/auth/components/AuthPage";
import { SignInForm } from "@/features/auth/components/SignInForm";
import { SignInNotice } from "@/features/auth/components/SignInNotice";

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

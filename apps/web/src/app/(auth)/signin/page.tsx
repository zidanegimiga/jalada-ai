import { Suspense } from "react";

import { AuthPage } from "@/features/auth/components/AuthPage";
import { SignInForm } from "@/features/auth/components/SignInForm";
import { SignInNotice } from "@/features/auth/components/SignInNotice";

export default function SignInPage() {
  return (
    <AuthPage
      mode="signin"
      title="Welcome"
      emphasis="back."
      intro="Sign in to your money records."
      notice={
        <Suspense>
          <SignInNotice />
        </Suspense>
      }
      footer={{
        text: "New here?",
        linkLabel: "Create an account",
        href: "/signup",
        destination: "Create account",
      }}
    >
      <SignInForm />
    </AuthPage>
  );
}

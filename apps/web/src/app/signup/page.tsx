import { AuthPage } from "@/features/auth/components/auth-page";
import { SignUpForm } from "@/features/auth/components/sign-up-form";

export default function SignUpPage() {
  return (
    <AuthPage
      title="Create your account"
      footer={{ text: "Already have an account?", linkLabel: "Sign in", href: "/signin" }}
    >
      <SignUpForm />
    </AuthPage>
  );
}

import { AuthPage } from "@/features/auth/components/AuthPage";
import { SignUpForm } from "@/features/auth/components/SignUpForm";

export default function SignUpPage() {
  return (
    <AuthPage
      title="Create your account"
      footer={{
        text: "Already have an account?",
        linkLabel: "Sign in",
        href: "/signin",
      }}
    >
      <SignUpForm />
    </AuthPage>
  );
}

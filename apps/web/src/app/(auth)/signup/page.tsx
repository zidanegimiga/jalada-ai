import { AuthPage } from "@/features/auth/components/AuthPage";
import { SignUpForm } from "@/features/auth/components/SignUpForm";

export default function SignUpPage() {
  return (
    <AuthPage
      mode="signup"
      title="Start your"
      emphasis="records."
      intro="Keep every M-Pesa message and receipt in one ledger, ready for your tax return."
      footer={{
        text: "Already have an account?",
        linkLabel: "Sign in",
        href: "/signin",
        destination: "Sign in",
      }}
    >
      <SignUpForm />
    </AuthPage>
  );
}

import { AuthPage } from "@/features/auth/components/auth-page";
import { SignInForm } from "@/features/auth/components/sign-in-form";

export default function SignInPage() {
  return (
    <AuthPage
      title="Welcome back"
      footer={{ text: "New here?", linkLabel: "Create an account", href: "/signup" }}
    >
      <SignInForm />
    </AuthPage>
  );
}

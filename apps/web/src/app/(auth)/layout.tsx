import { AuthHandoff } from "@/features/auth/components/Handoff";

import { AuthHeader } from "./_components/AuthHeader";

/** The frame around sign-in and sign-up. It stays in place when moving between the two. */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthHandoff>
      <div className="flex min-h-dvh flex-1 flex-col">
        <AuthHeader />
        {children}
      </div>
    </AuthHandoff>
  );
}

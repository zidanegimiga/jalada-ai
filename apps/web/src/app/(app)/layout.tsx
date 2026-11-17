import { AppShell } from "./_components/AppShell";

/** The frame around every signed-in page. It stays in place while pages change inside it. */
export default function AppLayout({ children }: LayoutProps<"/">) {
  return <AppShell>{children}</AppShell>;
}

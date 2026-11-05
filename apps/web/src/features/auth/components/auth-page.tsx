import Link from "next/link";
import { Suspense } from "react";

import { GoogleOption } from "./google-option";

type AuthPageProps = {
  title: string;
  notice?: React.ReactNode;
  children: React.ReactNode;
  footer: { text: string; linkLabel: string; href: string };
};

export function AuthPage({ title, notice, children, footer }: AuthPageProps) {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-8 px-4 py-12">
      <div className="flex flex-col gap-2">
        <p className="text-lg font-bold">Jalada AI</p>
        <h1 className="text-4xl font-bold">{title}</h1>
      </div>
      {notice}
      <Suspense>
        <GoogleOption />
      </Suspense>
      {children}
      <p className="text-center">
        {footer.text}{" "}
        <Link
          href={footer.href}
          className="font-medium underline underline-offset-4"
        >
          {footer.linkLabel}
        </Link>
      </p>
    </main>
  );
}

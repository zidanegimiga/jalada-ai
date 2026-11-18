import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { publicApiGet } from "@/shared/api/public-api";

export const metadata: Metadata = { title: "Privacy notice" };

// Where people write about their data. Set at build time; left out of the page when empty.
const CONTACT = process.env.PRIVACY_CONTACT ?? "";

type Service = { name: string; does: string; where: string; gets: string };

const SERVICES: Service[] = [
  {
    name: "Render",
    does: "Runs the app",
    where: "Frankfurt, Germany",
    gets: "Everything the app handles, while it handles it",
  },
  {
    name: "Neon",
    does: "Keeps the database",
    where: "Frankfurt, Germany (Amazon Web Services)",
    gets: "Your account and your records",
  },
  {
    name: "Cloudflare R2",
    does: "Keeps the files you send",
    where: "Outside Kenya",
    gets: "Your files, encrypted by the app first. The keys stay with the app.",
  },
  {
    name: "Netlify",
    does: "Serves the web pages",
    where: "Outside Kenya",
    gets: "Requests to the pages, as any website receives",
  },
  {
    name: "Sentry",
    does: "Reports errors in the app",
    where: "Outside Kenya",
    gets: "What went wrong in the code, without your records, messages or requests",
  },
  {
    name: "Google",
    does: "Signs you in, if you choose it",
    where: "Outside Kenya",
    gets: "That you are signing in to Jalada AI",
  },
  {
    name: "Telegram",
    does: "Carries what you send the bot, if you link it",
    where: "Outside Kenya",
    gets: "The receipts, messages and questions you send there",
  },
];

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-title">{title}</h2>
      <div className="flex flex-col gap-3 text-muted-foreground">
        {children}
      </div>
    </section>
  );
}

export default async function PrivacyPage() {
  const privacy = await publicApiGet<{ model_provider: string | null }>(
    "/v1/privacy",
  );
  const provider = privacy?.model_provider ?? null;
  const services = provider
    ? [
        ...SERVICES,
        {
          name: "Language model provider",
          does: "Reads photos and answers questions, only if you allow reading with AI",
          where: "Outside Kenya",
          gets: `Your receipts, messages and questions. ${provider}`,
        },
      ]
    : SERVICES;

  return (
    <main className="mx-auto flex w-full max-w-content flex-col gap-section px-gutter pt-6 pb-16">
      <div className="flex flex-col gap-2">
        <h1 className="text-display">Privacy notice</h1>
        <p className="text-muted-foreground">Last updated 18 November 2026.</p>
      </div>

      <Section title="What Jalada AI keeps">
        <p>
          Your name and email, and a password hash or your Google sign-in. The
          receipts, PDFs and M-Pesa messages you send, encrypted before they are
          stored. The records read from them and every change you make. If you
          use them, your Telegram link and your questions to the assistant with
          its answers.
        </p>
        <p>
          Logs and traces name what the app did and how long it took. They do
          not hold your records, messages or questions.
        </p>
      </Section>

      <Section title="Why">
        <p>
          To keep your money records and prepare your tax-year workbook, which
          is the service you sign up for. Reading your evidence and questions
          with a language model happens only if you allow it, and you can stop
          it at any time on your Account page.
        </p>
      </Section>

      <Section title="Where your data goes">
        <p>
          Jalada AI runs on these services. All of them are outside Kenya, so
          using the app means your data leaves Kenya. Each is bound by its own
          data processing terms.
        </p>
        <ul className="flex flex-col gap-3">
          {services.map((service) => (
            <li
              key={service.name}
              className="flex flex-col gap-1 rounded-card border border-border bg-card p-4"
            >
              <p className="font-medium text-foreground">
                {service.name}{" "}
                <span className="font-normal text-muted-foreground">
                  · {service.where}
                </span>
              </p>
              <p>{service.does}.</p>
              <p className="text-small">Receives: {service.gets}</p>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="How long it is kept">
        <p>
          Until you delete it. Deleting your account removes your account,
          records, files, conversations and links from the app at once.
        </p>
      </Section>

      <Section title="Your rights">
        <p>Under the Data Protection Act, 2019, you can:</p>
        <ul className="list-disc pl-5">
          <li>download everything held about you, from your Account page;</li>
          <li>correct any record, on the payment&apos;s own page;</li>
          <li>delete your account and everything in it;</li>
          <li>stop reading with AI at any time, on your Account page;</li>
          <li>
            complain to the{" "}
            <a
              href="https://www.odpc.go.ke"
              className="underline underline-offset-4"
            >
              Office of the Data Protection Commissioner
            </a>
            .
          </li>
        </ul>
        {CONTACT && (
          <p>
            To ask about your data, write to{" "}
            <a
              href={`mailto:${CONTACT}`}
              className="underline underline-offset-4"
            >
              {CONTACT}
            </a>
            .
          </p>
        )}
      </Section>

      <Section title="Changes">
        <p>
          If the language model provider changes, you are asked again before
          anything of yours goes to the new one.
        </p>
      </Section>

      <Link
        href="/signin"
        className="inline-flex min-h-tap items-center self-start underline underline-offset-4"
      >
        Back to Jalada AI
      </Link>
    </main>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { AppShell } from "@/components/app-shell";
import { CertificatePayments } from "@/features/certificates/components/certificate-payments";
import { getCertificate } from "@/features/certificates/server/get-certificate";

async function Details({ params }: { params: Promise<{ id: string }> }) {
  const data = await getCertificate((await params).id);
  if (!data) notFound();
  return <CertificatePayments data={data} />;
}

// The address holds the certificate's id, so the whole page, navigation included, is
// rendered on request.
export default function CertificatePage({
  params,
}: PageProps<"/ledger/certificates/[id]">) {
  return (
    <Suspense>
      <AppShell>
        <Link href="/ledger" className="underline underline-offset-4">
          Back to the ledger
        </Link>
        <h1 className="text-4xl font-bold">Withholding certificate</h1>
        <Suspense
          fallback={<p className="text-muted-foreground">Loading...</p>}
        >
          <Details params={params} />
        </Suspense>
      </AppShell>
    </Suspense>
  );
}

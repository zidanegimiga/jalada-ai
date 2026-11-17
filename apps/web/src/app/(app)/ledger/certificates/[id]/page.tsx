import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { Spinner } from "@/shared/components/Spinner";
import { CertificatePayments } from "@/features/certificates/components/CertificatePayments";
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
    <div className="mx-auto flex w-full max-w-content flex-col gap-section">
      <Suspense>
        <Link href="/ledger" className="underline underline-offset-4">
          Back to the ledger
        </Link>
        <h1 className="text-display">Withholding certificate</h1>
        <Suspense fallback={<Spinner />}>
          <Details params={params} />
        </Suspense>
      </Suspense>
    </div>
  );
}

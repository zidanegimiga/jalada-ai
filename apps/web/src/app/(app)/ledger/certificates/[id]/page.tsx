import { notFound } from "next/navigation";
import { Suspense } from "react";

import { Spinner } from "@/shared/components/Spinner";
import { CertificatePayments } from "@/features/certificates/components/CertificatePayments";
import { getCertificate } from "@/features/certificates/server/get-certificate";
import { PageHeader } from "@/app/(app)/_components/PageHeader";

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
        <PageHeader
          title="Withholding certificate"
          back={{ href: "/ledger", label: "Ledger" }}
        />
        <Suspense fallback={<Spinner />}>
          <Details params={params} />
        </Suspense>
      </Suspense>
    </div>
  );
}

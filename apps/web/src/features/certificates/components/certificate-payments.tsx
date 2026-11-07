"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatDay, formatKsh } from "@/lib/format";

import { linkPayment, unlinkPayment } from "../api";
import type { Certificate } from "../types";
import { describe, PaymentRow } from "./payment-row";

const LIST =
  "flex flex-col divide-y divide-border rounded-3xl border border-border bg-card";

/** Links a withholding certificate to the deposits that paid it, so income counts once. */
export function CertificatePayments({ data }: { data: Certificate }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const { certificate, payments, suggestions } = data;

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      router.refresh();
    } catch (caught) {
      setError((caught as Error).message);
    }
  }

  return (
    <>
      <section className="flex flex-col gap-1 rounded-3xl border border-border bg-card p-5">
        <p className="text-2xl font-bold">
          {formatKsh(certificate.amount_cents ?? 0)}
        </p>
        <p className="text-muted-foreground">
          {certificate.counterparty ?? "Unknown payer"}
          {certificate.occurred_on
            ? ` · ${formatDay(certificate.occurred_on)}`
            : ""}
        </p>
        <p>
          Tax withheld {formatKsh(certificate.tax_withheld_cents ?? 0)}, so they
          would have paid you {formatKsh(data.expected_payment_cents)}.
        </p>
      </section>
      <section aria-labelledby="linked-heading" className="flex flex-col gap-3">
        <h2 id="linked-heading" className="text-xl font-bold">
          Payments for this certificate
        </h2>
        {payments.length === 0 ? (
          <p className="text-muted-foreground">
            None linked yet. Until you link the payment, the workbook counts
            this income twice.
          </p>
        ) : (
          <ul className={LIST}>
            {payments.map((payment) => (
              <PaymentRow
                key={payment.id}
                payment={payment}
                action={
                  <Button
                    variant="outline"
                    aria-label={`Unlink ${describe(payment)}`}
                    onClick={() =>
                      run(() => unlinkPayment(certificate.id, payment.id))
                    }
                  >
                    Unlink
                  </Button>
                }
              />
            ))}
          </ul>
        )}
      </section>
      {suggestions.length > 0 && (
        <section
          aria-labelledby="suggested-heading"
          className="flex flex-col gap-3"
        >
          <h2 id="suggested-heading" className="text-xl font-bold">
            Could be the payment
          </h2>
          <ul className={LIST}>
            {suggestions.map((payment) => (
              <PaymentRow
                key={payment.id}
                payment={payment}
                action={
                  <Button
                    aria-label={`Link ${describe(payment)}`}
                    onClick={() =>
                      run(() => linkPayment(certificate.id, payment.id))
                    }
                  >
                    Link
                  </Button>
                }
              />
            ))}
          </ul>
        </section>
      )}
      {error && (
        <p role="alert" className="text-destructive">
          {error}
        </p>
      )}
    </>
  );
}

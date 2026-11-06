import type { ReactNode } from "react";

import type { Entry } from "@/features/review/types";
import { formatDay, formatKsh } from "@/lib/format";

/** "KSh 38,000.00 from CLIENT on 5 Mar 2026", to name a payment in a button label. */
export function describe(payment: Entry): string {
  const from = payment.counterparty ? ` from ${payment.counterparty}` : "";
  const on = payment.occurred_on ? ` on ${formatDay(payment.occurred_on)}` : "";
  return `${formatKsh(payment.amount_cents ?? 0)}${from}${on}`;
}

/** One deposit, with the action that links or unlinks it. */
export function PaymentRow({
  payment,
  action,
}: {
  payment: Entry;
  action: ReactNode;
}) {
  return (
    <li className="flex items-center justify-between gap-3 px-4 py-4">
      <div className="flex min-w-0 flex-col">
        <span className="font-bold">
          {formatKsh(payment.amount_cents ?? 0)}
        </span>
        <span className="truncate text-sm text-muted-foreground">
          {payment.counterparty ?? "Unknown"}
          {payment.occurred_on ? ` · ${formatDay(payment.occurred_on)}` : ""}
        </span>
      </div>
      {action}
    </li>
  );
}

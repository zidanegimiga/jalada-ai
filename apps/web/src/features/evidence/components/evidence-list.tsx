import { FileText, Image as ImageIcon, MessageSquareText } from "lucide-react";

import type { EvidenceItem } from "../api";

// Every status the API can send has a label: a new one fails the type check until it does.
const STATUS_LABELS: Record<EvidenceItem["status"], string> = {
  received: "Waiting to be read",
  processing: "Reading",
  proposed: "Ready to check",
  needs_review: "Needs a look",
  confirmed: "Saved to ledger",
  duplicate: "Already recorded",
  linked: "Linked to a payment",
  failed: "Could not read",
  not_a_transaction: "Not a transaction",
};

function describe(item: EvidenceItem) {
  if (item.content_type.startsWith("text/"))
    return { label: "Message", Icon: MessageSquareText };
  if (item.content_type === "application/pdf")
    return { label: "PDF", Icon: FileText };
  return { label: "Photo", Icon: ImageIcon };
}

const dateFormat = new Intl.DateTimeFormat("en-KE", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function EvidenceList({ items }: { items: EvidenceItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-muted-foreground">
        Nothing yet. Add a receipt or an M-Pesa message.
      </p>
    );
  }
  return (
    <ul className="flex flex-col divide-y divide-border rounded-3xl border border-border bg-card">
      {items.map((item) => {
        const { label, Icon } = describe(item);
        return (
          <li key={item.id} className="flex items-center gap-4 px-4 py-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-secondary">
              <Icon aria-hidden="true" className="size-5" />
            </span>
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="font-medium">{label}</span>
              <span className="text-sm text-muted-foreground">
                {dateFormat.format(new Date(item.received_at))}
              </span>
            </div>
            <div className="flex flex-col items-end gap-1 text-sm">
              <span>{STATUS_LABELS[item.status]}</span>
              <a
                href={`/v1/evidence/${item.id}/file`}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-4"
                aria-label={`Open ${label.toLowerCase()}`}
              >
                Open
              </a>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

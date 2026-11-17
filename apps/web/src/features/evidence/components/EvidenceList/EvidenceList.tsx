import {
  FileText,
  Image as ImageIcon,
  Inbox,
  MessageSquareText,
} from "lucide-react";

import { EmptyState } from "@/shared/components/EmptyState";

import type { EvidenceItem } from "../../api/evidence.api";
import { EvidenceDialog } from "../EvidenceDialog";
import { PutBack } from "../PutBack";

// Every status the API can send has a label: a new one fails the type check until it does.
const STATUS_LABELS: Record<EvidenceItem["status"], string> = {
  received: "Waiting to be read",
  processing: "Reading",
  proposed: "Ready to check",
  needs_review: "Needs a look",
  confirmed: "Saved to ledger",
  duplicate: "Already recorded",
  linked: "Linked to a payment",
  candidate: "Waiting for its payment",
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

/** Whether the Telegram bot is on for this site, and linked to this user. */
export type TelegramState = "off" | "unlinked" | "linked";

const TELEGRAM_TIP: Record<TelegramState, string | null> = {
  off: null,
  unlinked:
    "You can also send them from Telegram once you link it on the Account page.",
  linked: "You can also send them to the Jalada AI bot on Telegram.",
};

export function EvidenceList({
  items,
  telegram = "off",
}: {
  items: EvidenceItem[];
  telegram?: TelegramState;
}) {
  if (items.length === 0) {
    const tip = TELEGRAM_TIP[telegram];
    return (
      <EmptyState Icon={Inbox} title="Nothing here yet">
        <ol className="flex list-decimal flex-col gap-1 pl-5 text-left">
          <li>Paste an M-Pesa message or add a photo of a receipt above.</li>
          <li>
            Jalada AI reads it. Anything it is unsure of waits on To check.
          </li>
          <li>Once you confirm it, it goes into your ledger.</li>
        </ol>
        {tip && <p>{tip}</p>}
      </EmptyState>
    );
  }
  return (
    <ul className="flex flex-col divide-y divide-border rounded-card border border-border bg-card">
      {items.map((item) => {
        const { label, Icon } = describe(item);
        return (
          <li key={item.id} className="flex items-center gap-4 px-4 py-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-inset bg-secondary">
              <Icon aria-hidden="true" className="size-icon" />
            </span>
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="font-medium">{label}</span>
              <span className="text-small text-muted-foreground">
                {dateFormat.format(new Date(item.received_at))}
              </span>
            </div>
            <div className="flex flex-col items-end gap-1 text-small">
              <span>{STATUS_LABELS[item.status]}</span>
              <EvidenceDialog
                evidenceId={item.id}
                contentType={item.content_type}
                description={`Received ${dateFormat.format(new Date(item.received_at))}`}
                trigger={
                  <button
                    type="button"
                    className="inline-flex min-h-tap min-w-tap items-center justify-end underline underline-offset-4"
                  >
                    <span aria-hidden="true">Open</span>
                    <span className="sr-only">Open {label.toLowerCase()}</span>
                  </button>
                }
              />
              {item.status === "not_a_transaction" && <PutBack id={item.id} />}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

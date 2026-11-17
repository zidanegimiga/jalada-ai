import { FileText, Image as ImageIcon, MessageSquareText } from "lucide-react";

import { EvidenceDialog } from "@/features/evidence/components/EvidenceDialog";

import { describeEvidence } from "../../history";
import type { LinkedEvidence } from "../../types";

const RECEIVED = new Intl.DateTimeFormat("en-KE", {
  dateStyle: "medium",
  timeStyle: "short",
});

function iconFor(contentType: string) {
  if (contentType.startsWith("text/")) return MessageSquareText;
  return contentType === "application/pdf" ? FileText : ImageIcon;
}

/** Every message, receipt and document kept with the payment, each opening in a sheet. */
export function EntryEvidence({ evidence }: { evidence: LinkedEvidence[] }) {
  return (
    <section aria-labelledby="evidence-heading" className="flex flex-col gap-3">
      <h2 id="evidence-heading" className="text-title">
        Evidence
      </h2>
      {evidence.length === 0 ? (
        <p className="text-muted-foreground">
          Entered by hand, with nothing attached.
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-card border border-border bg-card">
          {evidence.map((link) => {
            const Icon = iconFor(link.content_type);
            const { title, detail } = describeEvidence(link);
            const received = `Received ${RECEIVED.format(new Date(link.received_at))}`;
            return (
              <li key={link.id}>
                <EvidenceDialog
                  evidenceId={link.id}
                  contentType={link.content_type}
                  description={received}
                  trigger={
                    <button
                      type="button"
                      className="flex w-full items-center gap-4 px-4 py-4 text-left transition-colors hover:bg-muted"
                    >
                      <span className="flex size-11 shrink-0 items-center justify-center rounded-inset bg-secondary text-secondary-foreground">
                        <Icon aria-hidden="true" className="size-icon" />
                      </span>
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className="font-medium">
                          {title}
                          <span className="sr-only">{", "}</span>
                        </span>
                        <span className="text-small text-muted-foreground">
                          {detail} · {received}
                        </span>
                      </span>
                      <span
                        aria-hidden="true"
                        className="text-small font-medium underline underline-offset-4"
                      >
                        Open
                      </span>
                    </button>
                  }
                />
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

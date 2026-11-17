import type { HistoryItem, LinkedEvidence } from "./types";

/** Who did it, as the timeline says it. The pipeline and the system are both Jalada AI. */
function by(actor: HistoryItem["actor"]): string {
  return actor === "user" ? "by you" : "by Jalada AI";
}

const ACTIONS: Record<HistoryItem["action"], (item: HistoryItem) => string> = {
  proposed: (i) => `Read ${by(i.actor)}`,
  entered: (i) => `Entered ${by(i.actor)}`,
  confirmed: (i) => `Confirmed ${by(i.actor)}`,
  corrected: (i) => `Changed ${by(i.actor)}`,
  rejected: (i) => `Marked not a transaction ${by(i.actor)}`,
  linked: (i) => `Evidence linked ${by(i.actor)}`,
  merged: () => "A receipt was joined to this payment",
  answered: () => "You answered a question about it",
  restored: () => "Put back on To check",
  unlinked: (i) => `Evidence unlinked ${by(i.actor)}`,
};

/** "amount", "category" as "the amount and the category". */
function listed(words: string[]): string {
  const named = words.map((word) => `the ${word}`);
  if (named.length < 2) return named.join("");
  return `${named.slice(0, -1).join(", ")} and ${named.at(-1)}`;
}

/** One event in plain words, with what it changed when it changed anything. */
export function describeEvent(item: HistoryItem): {
  title: string;
  detail?: string;
} {
  const title = ACTIONS[item.action](item);
  return item.changed.length
    ? { title, detail: `Changed ${listed(item.changed)}` }
    : { title };
}

const ROLES: Record<LinkedEvidence["role"], string> = {
  payment_proof: "Payment message",
  receipt: "Receipt",
  invoice: "Invoice",
  certificate: "Certificate",
  payslip: "Payslip",
  statement: "Statement",
  other: "Evidence",
};

const LINKED_BY: Record<LinkedEvidence["linked_by"], string> = {
  pipeline: "Read from it",
  exact: "Matched by its M-Pesa code",
  suggested: "A match you accepted",
  user: "Linked by you",
};

export function describeEvidence(link: LinkedEvidence): {
  title: string;
  detail: string;
} {
  return { title: ROLES[link.role], detail: LINKED_BY[link.linked_by] };
}

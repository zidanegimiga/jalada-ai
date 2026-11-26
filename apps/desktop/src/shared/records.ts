/** An entry as the window shows it, read from this computer's database. */
export type LocalEntry = {
  id: string;
  status: string;
  occurredOn: string | null;
  direction: "in" | "out" | null;
  amountCents: number | null;
  counterparty: string | null;
  categoryName: string | null;
  purpose: string;
};

/**
 * Where a change made on this computer is (decision 0029): kept here, on its way, accepted
 * by the server, or refused and waiting for the person.
 */
export type ChangeState = "saved" | "sending" | "confirmed" | "needs_attention";

/** A change as the window shows it. */
export type LocalChange = {
  id: string;
  summary: string;
  state: ChangeState;
  /** Why the server refused it, when it needs attention. */
  problem: string | null;
  createdAt: string;
};

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

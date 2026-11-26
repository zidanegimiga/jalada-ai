/** The request that carries one kind of change to the server. */
export type ChangeRequest = {
  method: "POST" | "PATCH";
  path: string;
  body: unknown;
};

/**
 * One kind of change people can make on this computer: how it is checked when made, shown
 * while it waits, and sent. A new kind is one more entry in CHANGE_KINDS.
 */
export type ChangeKind<Payload> = {
  /** The payload if it is acceptable, or null. Window input is never trusted. */
  accept: (input: unknown) => Payload | null;
  summary: (payload: Payload) => string;
  request: (payload: Payload) => ChangeRequest;
};

/** The API's own limit for pasted text. */
const MAX_PASTE_CHARACTERS = 5000;
const SUMMARY_CHARACTERS = 80;

type PastedMessage = { text: string };

/** An M-Pesa message, or any payment text, pasted in to be read like one sent from the web. */
const pastedMessage: ChangeKind<PastedMessage> = {
  accept: (input) => {
    const text = typeof input === "string" ? input.trim() : "";
    return text && text.length <= MAX_PASTE_CHARACTERS ? { text } : null;
  },
  summary: ({ text }) => {
    const line = text.replace(/\s+/g, " ");
    return line.length > SUMMARY_CHARACTERS
      ? `${line.slice(0, SUMMARY_CHARACTERS - 1)}…`
      : line;
  },
  request: ({ text }) => ({
    method: "POST",
    path: "/v1/evidence/text",
    body: { text },
  }),
};

/** Payloads come back from the database untyped; each kind only ever reads its own. */
function registered<Payload>(kind: ChangeKind<Payload>): ChangeKind<unknown> {
  return kind as ChangeKind<unknown>;
}

export const CHANGE_KINDS: Record<string, ChangeKind<unknown>> = {
  pasted_message: registered(pastedMessage),
};

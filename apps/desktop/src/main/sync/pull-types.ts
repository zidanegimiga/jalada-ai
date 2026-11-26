import type { OpenStore } from "../store/local-store";

/** How a pull ended. Only "pulled" changes what is on this computer. */
export type PullResult =
  | { outcome: "pulled"; entries: number; at: string }
  | { outcome: "signed-out" }
  | { outcome: "unreachable" };

/** When the copy here was last brought up to date. */
export const LAST_PULLED = "ledger_pulled_at";

export type Pull = {
  apiOrigin: string;
  token: string;
  store: OpenStore;
  fetch: (url: string, init: RequestInit) => Promise<Response>;
  now: () => Date;
};

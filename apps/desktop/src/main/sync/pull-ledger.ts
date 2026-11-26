import { copyWholeLedger } from "./copy-ledger";
import { followFeed } from "./follow-feed";
import type { Pull, PullResult } from "./pull-types";

export { LAST_PULLED, type Pull, type PullResult } from "./pull-types";

/**
 * Brings the ledger on this computer up to date: from the change feed, or, from a server
 * that does not have it yet, by copying the whole ledger again.
 */
export async function pullLedger(pull: Pull): Promise<PullResult> {
  const read = await followFeed(pull);
  return read.outcome === "missing" ? copyWholeLedger(pull) : read;
}

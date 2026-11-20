import type { Connection } from "@shared/bridge";

import { day, signedAmount, updatedLine } from "./format";
import { useLedger } from "./useLedger";

/**
 * The person's confirmed entries, read from this computer (decision 0029). Offline it says
 * so and keeps showing the last copy; online it can be refreshed.
 */
export function LedgerView({ connection }: { connection: Connection | null }) {
  const { entries, status, refresh } = useLedger();
  if (!status) return null;
  const offline = connection === "offline";

  return (
    <section aria-labelledby="ledger-heading" className="ledger">
      <header className="ledger-header">
        <h2 id="ledger-heading">Ledger</h2>
        <p className="muted small-text" role="status">
          {status.updating
            ? "Updating from the server"
            : updatedLine(status.updatedAt)}
          {offline && " · Offline, showing the copy on this computer"}
        </p>
        <button
          type="button"
          className="button button-quiet"
          onClick={refresh}
          disabled={offline || status.updating}
        >
          Refresh
        </button>
      </header>
      {entries.length === 0 ? (
        <p className="muted">
          {status.updatedAt
            ? "No confirmed entries yet. Entries you confirm on the web or in Telegram appear here."
            : "Your ledger appears here once it has been copied from the server."}
        </p>
      ) : (
        <ol className="ledger-rows">
          {entries.map((entry) => (
            <li key={entry.id} className="ledger-row">
              <span className="ledger-who">
                <strong>{entry.counterparty ?? "Unknown"}</strong>
                <span className="muted small-text">
                  {day(entry.occurredOn)} ·{" "}
                  {entry.categoryName ?? "No category"}
                </span>
              </span>
              <span
                className="ledger-amount"
                data-direction={entry.direction ?? "none"}
              >
                {signedAmount(entry)}
              </span>
            </li>
          ))}
        </ol>
      )}
      {status.entries > entries.length && (
        <p className="muted small-text">
          Showing the newest {entries.length} of {status.entries}.
        </p>
      )}
    </section>
  );
}

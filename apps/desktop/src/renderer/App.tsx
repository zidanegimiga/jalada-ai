import { useEffect, useState } from "react";

import type { AppInfo } from "@shared/bridge";

import { AccountPanel } from "./AccountPanel";
import { LedgerView } from "./LedgerView";
import { useAccount } from "./useAccount";
import { useConnection } from "./useConnection";

const CONNECTION_TEXT = {
  online: "Online. The copy here is kept up to date.",
  offline: "Offline. You are reading the copy kept on this computer.",
};

/**
 * The desktop app's frame: who is signed in, and their ledger read from this computer.
 * Changes made here, queued while offline, arrive in the next step (decision 0029).
 */
export function App() {
  const connection = useConnection();
  const accountState = useAccount();
  const [info, setInfo] = useState<AppInfo | null>(null);

  useEffect(() => {
    void window.jalada.app.info().then(setInfo);
  }, []);

  return (
    <main className="frame">
      <header className="frame-header">
        <p className="brand">Jalada AI</p>
        {connection && (
          <p role="status" className="connection" data-connection={connection}>
            <span aria-hidden="true" className="connection-dot" />
            {connection === "online" ? "Online" : "Offline"}
          </p>
        )}
      </header>
      <section className="welcome">
        <h1>Your records, on this computer</h1>
        <p>
          The desktop app keeps a copy of your records here, encrypted, so you
          can read them and add new ones without a connection.
        </p>
        {connection && <p className="muted">{CONNECTION_TEXT[connection]}</p>}
      </section>
      <AccountPanel state={accountState} />
      {accountState.account && <LedgerView connection={connection} />}
      {info && (
        <footer className="muted small">
          Version {info.version}. Syncs with {info.apiOrigin}.
        </footer>
      )}
    </main>
  );
}

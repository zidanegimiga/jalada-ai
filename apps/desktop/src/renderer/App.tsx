import { useEffect, useState } from "react";

import type { AppInfo } from "@shared/bridge";

import { useConnection } from "./useConnection";

const CONNECTION_TEXT = {
  online: "Online. Changes go to the server as you make them.",
  offline:
    "Offline. Changes stay on this computer until the connection returns.",
};

/**
 * The desktop app's frame. Sign-in, the ledger read from this computer and the queue of
 * changes arrive in the next steps (decision 0029).
 */
export function App() {
  const connection = useConnection();
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
      {info && (
        <footer className="muted small">
          Version {info.version}. Syncs with {info.apiOrigin}.
        </footer>
      )}
    </main>
  );
}

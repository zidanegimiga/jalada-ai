import { useState } from "react";

import type { AccountState } from "./useAccount";
import { WaitingForBrowser } from "./WaitingForBrowser";

/**
 * Signing in through the browser, where passwords, Google and passkeys already work, and
 * signing out, which also removes this person's records from the computer.
 */
export function AccountPanel({
  state,
  unsent,
}: {
  state: AccountState;
  /** Changes the server does not have yet, which signing out would lose. */
  unsent: number;
}) {
  const { account, failure, waiting, signIn, cancel, paste } = state;
  if (account === undefined) return null;
  if (account) return <SignedIn state={state} unsent={unsent} />;

  return (
    <section className="panel">
      <p>Sign in with your browser to keep your records on this computer.</p>
      <button
        type="button"
        className="button"
        onClick={signIn}
        disabled={waiting}
      >
        {waiting ? "Waiting for your browser" : "Sign in with your browser"}
      </button>
      {waiting && <WaitingForBrowser cancel={cancel} paste={paste} />}
      {failure && (
        <p role="alert" className="failure">
          {failure}
        </p>
      )}
    </section>
  );
}

/** Who is signed in, and signing out, asked twice when changes would be lost. */
function SignedIn({ state, unsent }: { state: AccountState; unsent: number }) {
  const [asked, setAsked] = useState(false);
  const account = state.account;
  if (!account) return null;
  const warn = unsent > 0 && !asked;

  return (
    <section className="panel panel-row">
      <p>
        Signed in as <strong>{account.name}</strong> ({account.email}).
      </p>
      {asked && (
        <p role="alert" className="failure">
          {unsent === 1 ? "1 change has" : `${unsent} changes have`} not reached
          the server yet and will be lost. Connect first to keep{" "}
          {unsent === 1 ? "it" : "them"}.
        </p>
      )}
      <button
        type="button"
        className="button button-quiet"
        onClick={warn ? () => setAsked(true) : state.signOut}
      >
        {asked
          ? "Sign out anyway"
          : "Sign out and remove records from this computer"}
      </button>
    </section>
  );
}

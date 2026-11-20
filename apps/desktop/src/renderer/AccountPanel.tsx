import type { AccountState } from "./useAccount";

/**
 * Signing in through the browser, where passwords, Google and passkeys already work, and
 * signing out, which also removes this person's records from the computer.
 */
export function AccountPanel({ state }: { state: AccountState }) {
  const { account, failure, waiting, signIn, signOut } = state;
  if (account === undefined) return null;

  if (account) {
    return (
      <section className="panel panel-row">
        <p>
          Signed in as <strong>{account.name}</strong> ({account.email}).
        </p>
        <button type="button" className="button button-quiet" onClick={signOut}>
          Sign out and remove records from this computer
        </button>
      </section>
    );
  }

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
      {failure && (
        <p role="alert" className="failure">
          {failure}
        </p>
      )}
    </section>
  );
}

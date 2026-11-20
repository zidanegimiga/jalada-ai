import { useEffect, useState } from "react";

import type { Account } from "@shared/bridge";

export type AccountState = {
  /** Undefined while the main process is asked; null when nobody is signed in. */
  account: Account | null | undefined;
  /** Why the last sign-in through the browser failed, until the next attempt. */
  failure: string | null;
  waiting: boolean;
  signIn: () => void;
  signOut: () => void;
  /** Stops waiting for the browser. */
  cancel: () => void;
  /** Finishes sign-in with the link the web page shows when the app did not open. */
  paste: (link: string) => void;
};

/** Who is signed in on this computer, kept up to date, with sign-in and sign-out. */
export function useAccount(): AccountState {
  const [account, setAccount] = useState<Account | null | undefined>(undefined);
  const [failure, setFailure] = useState<string | null>(null);
  const [waiting, setWaiting] = useState(false);

  useEffect(() => {
    let live = true;
    void window.jalada.account.current().then((now) => {
      if (live) setAccount(now);
    });
    const stopChanges = window.jalada.account.onChange((now) => {
      setAccount(now);
      setWaiting(false);
    });
    // A failed attempt, such as a mistyped link, keeps the wait open to try again; the
    // main process ends it when time runs out, through onChange.
    const stopFailures = window.jalada.account.onFailed(setFailure);
    return () => {
      live = false;
      stopChanges();
      stopFailures();
    };
  }, []);

  return {
    account,
    failure,
    waiting,
    signIn: () => {
      setFailure(null);
      setWaiting(true);
      void window.jalada.account.signIn();
    },
    signOut: () => void window.jalada.account.signOut(),
    cancel: () => {
      setWaiting(false);
      void window.jalada.account.cancelSignIn();
    },
    paste: (link) => {
      setFailure(null);
      void window.jalada.account.pasteSignInLink(link);
    },
  };
}

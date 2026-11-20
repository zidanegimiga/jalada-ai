import { useState, type FormEvent } from "react";

/**
 * While the browser is asked: a way to stop waiting, and to finish by hand when the browser
 * could not open the app. The web page then shows the sign-in link to copy.
 */
export function WaitingForBrowser({
  cancel,
  paste,
}: {
  cancel: () => void;
  paste: (link: string) => void;
}) {
  const [link, setLink] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (link.trim()) paste(link);
  }

  return (
    <div className="waiting">
      <p className="muted">
        Allow the sign-in in your browser. If the app does not open by itself,
        copy the sign-in link the page shows and paste it here.
      </p>
      <form className="paste" onSubmit={submit}>
        <label htmlFor="sign-in-link">Sign-in link</label>
        <input
          id="sign-in-link"
          value={link}
          onChange={(event) => setLink(event.target.value)}
          placeholder="jalada://signed-in?code=…"
          autoComplete="off"
          spellCheck={false}
        />
        <button type="submit" className="button" disabled={!link.trim()}>
          Finish signing in
        </button>
      </form>
      <button type="button" className="button button-quiet" onClick={cancel}>
        Cancel
      </button>
    </div>
  );
}

import { useState, type FormEvent } from "react";

import type { ChangeState, LocalChange } from "@shared/records";

import { moment } from "./format";

/** The API's own limit for pasted text. */
const MAX_CHARACTERS = 5000;

export const STATE_TEXT: Record<ChangeState, string> = {
  saved: "Saved on this computer",
  sending: "Sending",
  confirmed: "Sent",
  needs_attention: "Needs attention",
};

/**
 * Adding an M-Pesa message, online or not, and the changes made here with where each is
 * (decision 0029). A message is kept on this computer first and sent when there is a
 * connection.
 */
export function ChangesPanel({
  changes,
  pasteMessage,
}: {
  changes: LocalChange[];
  pasteMessage: (text: string) => Promise<boolean>;
}) {
  const [text, setText] = useState("");
  const [refused, setRefused] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const kept = await pasteMessage(text);
    setRefused(!kept);
    if (kept) setText("");
  }

  return (
    <section aria-labelledby="changes-heading" className="panel changes">
      <h2 id="changes-heading">Add an M-Pesa message</h2>
      <form className="paste-message" onSubmit={submit}>
        <label htmlFor="message">
          Paste the message as M-Pesa sent it. It is kept on this computer and
          sent when you are online.
        </label>
        <textarea
          id="message"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={MAX_CHARACTERS}
          rows={3}
          spellCheck={false}
        />
        <button type="submit" className="button" disabled={!text.trim()}>
          Save message
        </button>
      </form>
      {refused && (
        <p role="alert" className="failure">
          That message could not be kept. Paste the text of one message.
        </p>
      )}
      {changes.length > 0 && (
        <ol className="change-rows" aria-label="Your changes">
          {changes.map((change) => (
            <li key={change.id} className="change-row">
              <span className="change-what">
                {change.summary}
                <span className="muted small-text">
                  Added {moment(change.createdAt)}
                  {change.problem && ` · ${change.problem}`}
                </span>
              </span>
              <span className="change-state" data-state={change.state}>
                {STATE_TEXT[change.state]}
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

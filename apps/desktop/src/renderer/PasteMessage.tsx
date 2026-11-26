import { useState, type FormEvent } from "react";

/** The API's own limit for pasted text. */
const MAX_CHARACTERS = 5000;

/** Adding an M-Pesa message, kept on this computer first and sent when online. */
export function PasteMessage({
  pasteMessage,
}: {
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
      {refused && (
        <p role="alert" className="failure">
          That message could not be kept. Paste the text of one message.
        </p>
      )}
    </form>
  );
}

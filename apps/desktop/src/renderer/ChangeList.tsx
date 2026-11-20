import type { LocalChange } from "@shared/records";

import { STATE_TEXT } from "./change-summary";
import { moment } from "./format";

export type ChangeActions = {
  tryAgain: (id: string) => void;
  discard: (id: string) => void;
};

/** One group of changes, under its own heading, with what can be done to each. */
export function ChangeList({
  title,
  changes,
  actions,
}: {
  title: string;
  changes: LocalChange[];
  actions: ChangeActions;
}) {
  if (changes.length === 0) return null;
  return (
    <div className="change-group">
      <h3>{title}</h3>
      <ol className="change-rows" aria-label={title}>
        {changes.map((change) => (
          <ChangeRow key={change.id} change={change} actions={actions} />
        ))}
      </ol>
    </div>
  );
}

function ChangeRow({
  change,
  actions,
}: {
  change: LocalChange;
  actions: ChangeActions;
}) {
  const refused = change.state === "needs_attention";
  // One on its way may already be on the server, so it cannot be dropped.
  const canDiscard = refused || change.state === "saved";

  return (
    <li className="change-row">
      <span className="change-what">
        {change.summary}
        <span className="muted small-text">
          Added {moment(change.createdAt)}
        </span>
        {change.problem && (
          <span className="change-problem small-text">{change.problem}</span>
        )}
      </span>
      <span className="change-side">
        <span className="change-state" data-state={change.state}>
          {STATE_TEXT[change.state]}
        </span>
        {refused && (
          <button
            type="button"
            className="button button-small"
            onClick={() => actions.tryAgain(change.id)}
            aria-label={`Try again: ${change.summary}`}
          >
            Try again
          </button>
        )}
        {canDiscard && (
          <button
            type="button"
            className="button button-quiet button-small"
            onClick={() => actions.discard(change.id)}
            aria-label={`Discard: ${change.summary}`}
          >
            Discard
          </button>
        )}
      </span>
    </li>
  );
}

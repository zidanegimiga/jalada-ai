import type { Connection } from "@shared/bridge";
import type { LocalChange } from "@shared/records";

import { ChangeList, type ChangeActions } from "./ChangeList";
import { changeSummary, groupChanges } from "./change-summary";
import { PasteMessage } from "./PasteMessage";

/**
 * Adding an M-Pesa message, online or not, and the changes made here grouped by where each
 * is (decision 0029): what needs the person first, then what is waiting, then what went.
 */
export function ChangesPanel({
  changes,
  unsent,
  connection,
  pasteMessage,
  actions,
}: {
  changes: LocalChange[];
  unsent: number;
  connection: Connection | null;
  pasteMessage: (text: string) => Promise<boolean>;
  actions: ChangeActions;
}) {
  const groups = groupChanges(changes);

  return (
    <section aria-labelledby="changes-heading" className="panel changes">
      <h2 id="changes-heading">Add an M-Pesa message</h2>
      <PasteMessage pasteMessage={pasteMessage} />
      <p role="status" className="change-summary">
        {changeSummary(groups, unsent, connection)}
      </p>
      <ChangeList
        title="Needs attention"
        changes={groups.needsAttention}
        actions={actions}
      />
      <ChangeList
        title="Waiting to send"
        changes={groups.waiting}
        actions={actions}
      />
      <ChangeList
        title="Sent this week"
        changes={groups.sent}
        actions={actions}
      />
    </section>
  );
}

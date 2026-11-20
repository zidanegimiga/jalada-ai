import type { Connection } from "@shared/bridge";
import type { ChangeState, LocalChange } from "@shared/records";

export const STATE_TEXT: Record<ChangeState, string> = {
  saved: "Saved on this computer",
  sending: "Sending",
  confirmed: "Sent",
  needs_attention: "Needs attention",
};

/** The groups the list shows, most urgent first. */
export type ChangeGroups = {
  needsAttention: LocalChange[];
  waiting: LocalChange[];
  sent: LocalChange[];
};

export function groupChanges(changes: LocalChange[]): ChangeGroups {
  return {
    needsAttention: changes.filter((c) => c.state === "needs_attention"),
    waiting: changes.filter(
      (c) => c.state === "saved" || c.state === "sending",
    ),
    sent: changes.filter((c) => c.state === "confirmed"),
  };
}

const plural = (n: number, one: string, many: string) =>
  `${n} ${n === 1 ? one : many}`;

/**
 * One line on where things stand, read out when it changes: what needs the person, what
 * is waiting and for what, or that everything went.
 */
export function changeSummary(
  groups: ChangeGroups,
  unsent: number,
  connection: Connection | null,
): string {
  const parts: string[] = [];
  if (groups.needsAttention.length > 0) {
    parts.push(
      plural(groups.needsAttention.length, "change needs", "changes need") +
        " your attention",
    );
  }
  if (unsent > 0) {
    const sending = groups.waiting.some((c) => c.state === "sending");
    const when = sending
      ? "sending now"
      : connection === "offline"
        ? "will send when you are online"
        : "will send shortly";
    parts.push(`${plural(unsent, "change", "changes")} waiting, ${when}`);
  }
  if (parts.length > 0) return `${parts.join(". ")}.`;
  return groups.sent.length > 0
    ? "Everything you added here has reached the server."
    : "Nothing added on this computer yet.";
}

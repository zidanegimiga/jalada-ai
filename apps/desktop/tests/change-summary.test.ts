import { describe, expect, it } from "vitest";

import type { ChangeState, LocalChange } from "../src/shared/records";
import { changeSummary, groupChanges } from "../src/renderer/change-summary";

let n = 0;
function change(state: ChangeState): LocalChange {
  n += 1;
  return {
    id: `change-${n}`,
    summary: `Message ${n}`,
    state,
    problem: state === "needs_attention" ? "Refused." : null,
    createdAt: "2026-11-20T09:00:00.000Z",
  };
}

const unsentIn = (changes: LocalChange[]) =>
  changes.filter((c) => c.state === "saved" || c.state === "sending").length;

function summary(states: ChangeState[], connection: "online" | "offline") {
  const changes = states.map(change);
  return changeSummary(groupChanges(changes), unsentIn(changes), connection);
}

describe("where changes stand", () => {
  it("groups them, most urgent first", () => {
    const changes = (
      ["confirmed", "saved", "needs_attention", "sending"] as const
    ).map(change);

    const groups = groupChanges(changes);

    expect(groups.needsAttention.map((c) => c.state)).toEqual([
      "needs_attention",
    ]);
    expect(groups.waiting.map((c) => c.state)).toEqual(["saved", "sending"]);
    expect(groups.sent.map((c) => c.state)).toEqual(["confirmed"]);
  });

  it("says what needs the person and what waits for a connection", () => {
    expect(summary(["needs_attention", "saved", "saved"], "offline")).toBe(
      "1 change needs your attention. 2 changes waiting, will send when you are online.",
    );
  });

  it("says when one is on its way", () => {
    expect(summary(["sending"], "online")).toBe(
      "1 change waiting, sending now.",
    );
  });

  it("says when everything went, or nothing was added", () => {
    expect(summary(["confirmed"], "online")).toBe(
      "Everything you added here has reached the server.",
    );
    expect(summary([], "online")).toBe("Nothing added on this computer yet.");
  });
});

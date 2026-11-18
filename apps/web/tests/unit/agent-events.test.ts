import { describe, expect, it } from "vitest";

import { readEvents } from "@/features/agent/api/agent.api";

const progress =
  'event: progress\ndata: {"stage": "looking_up", "tool": "add_up_payments", "label": "Adding up your payments"}\n\n';
const answer =
  'event: answer\ndata: {"thread_id": "t-1", "text": "Ksh 4,500.", "outcome": "answered"}\n\n';

describe("readEvents", () => {
  it("reads every complete event", () => {
    const { events, rest } = readEvents(progress + answer);

    expect(events.map((e) => e.event)).toEqual(["progress", "answer"]);
    expect(events[1]).toEqual({
      event: "answer",
      data: { thread_id: "t-1", text: "Ksh 4,500.", outcome: "answered" },
    });
    expect(rest).toBe("");
  });

  it("keeps an event that is still arriving for the next read", () => {
    const half = answer.slice(0, 30);

    const first = readEvents(progress + half);
    const second = readEvents(first.rest + answer.slice(30));

    expect(first.events).toHaveLength(1);
    expect(first.rest).toBe(half);
    expect(second.events.map((e) => e.event)).toEqual(["answer"]);
  });

  it("skips an event it cannot read", () => {
    const { events } = readEvents(
      "event: progress\ndata: {not json\n\n" + answer,
    );

    expect(events.map((e) => e.event)).toEqual(["answer"]);
  });
});

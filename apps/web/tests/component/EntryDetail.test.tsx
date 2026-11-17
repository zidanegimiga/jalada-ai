import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EntryEvidence } from "@/features/ledger/components/EntryEvidence";
import { EntryHistory } from "@/features/ledger/components/EntryHistory";

describe("EntryHistory", () => {
  it("lists what happened, oldest first, with what a change touched", () => {
    render(
      <EntryHistory
        history={[
          {
            at: "2026-11-17T06:00:00Z",
            actor: "pipeline",
            action: "proposed",
            changed: [],
          },
          {
            at: "2026-11-17T09:00:00Z",
            actor: "user",
            action: "corrected",
            changed: ["amount"],
          },
        ]}
      />,
    );

    const events = screen.getAllByRole("listitem");
    expect(events[0]).toHaveTextContent("Read by Jalada AI");
    expect(events[1]).toHaveTextContent("Changed by you");
    expect(events[1]).toHaveTextContent("Changed the amount");
  });
});

describe("EntryEvidence", () => {
  it("offers each piece of evidence in a sheet, and says when there is none", () => {
    const { rerender } = render(
      <EntryEvidence
        evidence={[
          {
            id: "e1",
            role: "payment_proof",
            linked_by: "pipeline",
            linked_at: "2026-11-17T06:00:00Z",
            content_type: "text/plain",
            received_at: "2026-11-17T06:00:00Z",
          },
        ]}
      />,
    );

    expect(
      screen.getByRole("button", { name: /^Payment message,\s?Read from it/ }),
    ).toHaveAttribute("aria-haspopup", "dialog");

    rerender(<EntryEvidence evidence={[]} />);
    expect(
      screen.getByText("Entered by hand, with nothing attached."),
    ).toBeInTheDocument();
  });
});

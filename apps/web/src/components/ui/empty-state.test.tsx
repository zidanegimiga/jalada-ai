import { render, screen } from "@testing-library/react";
import { Inbox } from "lucide-react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./empty-state";

describe("EmptyState", () => {
  it("shows the title, the explanation and the next step", () => {
    render(
      <EmptyState
        Icon={Inbox}
        title="Nothing here yet"
        action={<button type="button">Add one</button>}
      >
        <p>Things you add appear here.</p>
      </EmptyState>,
    );

    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
    expect(screen.getByText("Things you add appear here.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add one" })).toBeInTheDocument();
  });
});

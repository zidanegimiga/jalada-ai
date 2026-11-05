import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EntryForm } from "./entry-form";
import { CATEGORIES, entry } from "./test-data";

function options() {
  return screen.getAllByRole("option").map((option) => option.textContent);
}

describe("EntryForm", () => {
  it("starts from what the pipeline read", () => {
    render(
      <EntryForm
        entry={entry()}
        categories={CATEGORIES}
        submitLabel="Save"
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Amount (KSh)")).toHaveValue("150.00");
    expect(screen.getByLabelText("Date")).toHaveValue("2026-11-04");
    expect(screen.getByLabelText("What it was for")).toHaveValue(
      "personal_food",
    );
  });

  it("only offers categories for the chosen direction", () => {
    render(
      <EntryForm
        entry={null}
        categories={CATEGORIES}
        submitLabel="Save"
        onSubmit={vi.fn()}
      />,
    );

    expect(options()).toEqual(["Choose one", "Food", "Stock and supplies"]);

    fireEvent.click(screen.getByRole("button", { name: "Money in" }));

    expect(options()).toEqual(["Choose one", "Salary"]);
    expect(screen.getByRole("button", { name: "Money in" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("sends the amount as text, without currency or spaces", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <EntryForm
        entry={entry()}
        categories={CATEGORIES}
        submitLabel="Save"
        onSubmit={onSubmit}
      />,
    );

    fireEvent.change(screen.getByLabelText("Amount (KSh)"), {
      target: { value: "KSh 1,250.00 " },
    });
    fireEvent.change(screen.getByLabelText("What it was for"), {
      target: { value: "business_stock" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(onSubmit.mock.calls[0][0]).toEqual({
      occurred_on: "2026-11-04",
      amount: "1,250.00",
      direction: "out",
      counterparty: "JANE WANJIKU",
      category: "business_stock",
    });
  });
});

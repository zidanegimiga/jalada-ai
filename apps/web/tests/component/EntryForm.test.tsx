import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EntryForm } from "@/features/review/components/EntryForm";
import { chooseOption } from "../support/choose";
import { CATEGORIES, entry } from "../support/review-fixtures";

/** The categories on offer: opens the list, reads it and closes it again. */
async function options() {
  const select = screen.getByRole("combobox", { name: "What it was for" });
  fireEvent.click(select);
  const found = (await screen.findAllByRole("option")).map(
    (option) => option.textContent,
  );
  fireEvent.keyDown(select, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("option")).toBeNull());
  return found;
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
    expect(
      screen.getByRole("combobox", { name: "What it was for" }),
    ).toHaveTextContent("Food");
  });

  it("only offers categories for the chosen direction", async () => {
    render(
      <EntryForm
        entry={null}
        categories={CATEGORIES}
        submitLabel="Save"
        onSubmit={vi.fn()}
      />,
    );

    expect(await options()).toEqual(["Food", "Stock and supplies"]);

    fireEvent.click(screen.getByRole("button", { name: "Money in" }));

    expect(await options()).toEqual(["Salary"]);
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
    await chooseOption("What it was for", "Stock and supplies");
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

describe("EntryForm on a page with several cards", () => {
  it("keeps each label tied to its own field", () => {
    render(
      <>
        <EntryForm
          entry={entry({ amount_cents: 100 })}
          categories={CATEGORIES}
          submitLabel="One"
          onSubmit={vi.fn()}
        />
        <EntryForm
          entry={entry({ amount_cents: 200 })}
          categories={CATEGORIES}
          submitLabel="Two"
          onSubmit={vi.fn()}
        />
      </>,
    );

    const amounts = screen.getAllByLabelText("Amount (KSh)");
    expect(amounts.map((field) => (field as HTMLInputElement).value)).toEqual([
      "1.00",
      "2.00",
    ]);
    expect(new Set(amounts.map((field) => field.id)).size).toBe(2);
  });
});

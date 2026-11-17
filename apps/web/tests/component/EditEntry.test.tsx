import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EditEntry } from "@/features/review/components/EditEntry";

import { chooseOption } from "../support/choose";
import { CATEGORIES, entry } from "../support/review-fixtures";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

function respond(status: number, body: unknown) {
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("EditEntry", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    refresh.mockReset();
  });

  it("saves a change as a correction, then shows it saved", async () => {
    const fetch = respond(200, entry());
    render(<EditEntry entry={entry()} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Edit this payment" }));
    await chooseOption("What it was for", "Stock and supplies");
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(refresh).toHaveBeenCalled());
    const [path, init] = fetch.mock.calls[0];
    expect(path).toBe(`/v1/entries/${entry().id}`);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body).category).toBe("business_stock");
    expect(screen.getByRole("status")).toHaveTextContent("Saved.");
  });

  it("keeps the form open and says why when the change is refused", async () => {
    respond(422, {
      error: { code: "invalid_entry", message: "Add the amount." },
    });
    render(<EditEntry entry={entry()} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Edit this payment" }));
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Add the amount."),
    );
    expect(
      screen.getByRole("heading", { name: "Edit this payment" }),
    ).toBeInTheDocument();
  });

  it("cancels without saving", () => {
    const fetch = respond(200, entry());
    render(<EditEntry entry={entry()} categories={CATEGORIES} />);

    fireEvent.click(screen.getByRole("button", { name: "Edit this payment" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(fetch).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Edit this payment" }),
    ).toBeInTheDocument();
  });
});

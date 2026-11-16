import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OwnAccountQuestion } from "./own-account-question";
import { entry } from "./test-data";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

describe("OwnAccountQuestion", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("makes the payment a transfer when the account is mine", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(entry()), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetch);
    render(<OwnAccountQuestion entryId="entry-1" direction="out" />);

    fireEvent.click(
      screen.getByRole("button", { name: "Yes, it is my account" }),
    );

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/payments/entry-1/own-account");
  });

  it("asks about money in as coming from the account", () => {
    render(<OwnAccountQuestion entryId="entry-1" direction="in" />);

    expect(
      screen.getByText(/Did this come from your own account\?/),
    ).toBeInTheDocument();
    expect(screen.getByText(/is not income/)).toBeInTheDocument();
  });

  it("shows why it did not save", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              message: "This payment was not to or from a business account.",
            },
          }),
          { status: 422 },
        ),
      ),
    );
    render(<OwnAccountQuestion entryId="entry-1" direction="out" />);

    fireEvent.click(
      screen.getByRole("button", { name: "Yes, it is my account" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This payment was not to or from a business account.",
    );
  });
});

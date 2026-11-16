import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OwnAccountNote } from "./own-account-note";
import { entry } from "./test-data";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

describe("OwnAccountNote", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("names the account and takes it back on Undo", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(entry()), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetch);
    render(
      <OwnAccountNote
        entryId="entry-1"
        account="SAMPLE BANK PAYBILL ending 6789"
        direction="out"
      />,
    );

    expect(
      screen.getByText("To your own account, SAMPLE BANK PAYBILL ending 6789."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe(
      "/v1/payments/entry-1/own-account/undo",
    );
  });

  it("shows why it did not take it back", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              message: "This is not a transfer waiting to be confirmed.",
            },
          }),
          { status: 422 },
        ),
      ),
    );
    render(
      <OwnAccountNote entryId="entry-1" account="SAMPLE BANK" direction="in" />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This is not a transfer waiting to be confirmed.",
    );
  });
});

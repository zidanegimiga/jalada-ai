import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConfirmAll } from "./confirm-all";
import { entry } from "./test-data";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const sent = entry({ id: "entry-1", amount_cents: 15000 });
const paid = entry({ id: "entry-2", amount_cents: 30000 });
const received = entry({
  id: "entry-3",
  amount_cents: 100000,
  direction: "in",
});

function answer(confirmed: unknown[]) {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ confirmed }), { status: 200 }),
    );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("ConfirmAll", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("says how much is about to be confirmed", () => {
    render(<ConfirmAll entries={[sent, paid, received]} />);

    expect(
      screen.getByText(
        /3 payments are ready: KSh 450.00 out, KSh 1,000.00 in\./,
      ),
    ).toBeInTheDocument();
  });

  it("sends only the payments it lists", async () => {
    const fetch = answer([sent, paid]);
    render(<ConfirmAll entries={[sent, paid]} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm all 2" }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch.mock.calls[0][0]).toBe("/v1/review/confirm-all");
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      entry_ids: ["entry-1", "entry-2"],
    });
  });

  it("says when a payment changed and was left for a look", async () => {
    answer([sent]);
    render(<ConfirmAll entries={[sent, paid]} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm all 2" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "1 payment changed and still needs a look.",
    );
  });
});

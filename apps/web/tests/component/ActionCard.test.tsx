import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ActionCard } from "@/features/agent/components/ActionCard";
import type { SuggestedAction } from "@/features/agent/types";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const TOMORROW = new Date(Date.now() + 86_400_000).toISOString();

function suggestion(changes: Partial<SuggestedAction> = {}): SuggestedAction {
  return {
    id: "action-1",
    kind: "change_category",
    summary:
      "Move Ksh 2,500.00 to KPLC PREPAID on 4 Jul 2026 to Workspace rent",
    status: "proposed",
    expires_at: TOMORROW,
    ...changes,
  };
}

function answers(status: number, body: unknown) {
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("ActionCard", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("shows what will change and changes nothing until Confirm", async () => {
    const fetch = answers(200, suggestion({ status: "confirmed" }));
    render(<ActionCard action={suggestion()} />);

    expect(
      screen.getByText(/Move Ksh 2,500.00 to KPLC PREPAID/),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByText("Done")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "/v1/assistant/actions/action-1/confirm",
      { method: "POST" },
    );
    expect(router.refresh).toHaveBeenCalled();
  });

  it("leaves things as they were when declined", async () => {
    const fetch = answers(200, suggestion({ status: "declined" }));
    render(<ActionCard action={suggestion()} />);

    fireEvent.click(screen.getByRole("button", { name: "Not now" }));

    expect(await screen.findByText("Left as it was")).toBeInTheDocument();
    expect(fetch.mock.calls[0][0]).toBe(
      "/v1/assistant/actions/action-1/decline",
    );
    expect(router.refresh).not.toHaveBeenCalled();
  });

  it("says why a change could not be made and keeps the buttons", async () => {
    answers(409, {
      error: { message: "That change was already confirmed or declined." },
    });
    render(<ActionCard action={suggestion()} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "already confirmed",
    );
    expect(screen.getByRole("button", { name: "Confirm" })).toBeEnabled();
  });

  it("offers no buttons once a suggestion has expired", () => {
    render(<ActionCard action={suggestion({ status: "expired" })} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText(/Expired/)).toBeInTheDocument();
  });
});

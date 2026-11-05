import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DeleteAccountForm } from "./delete-account-form";

const router = { replace: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function type(value: string) {
  fireEvent.change(screen.getByLabelText("Type jane@example.com to confirm"), {
    target: { value },
  });
}

describe("DeleteAccountForm", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("only works once the email is typed exactly", () => {
    render(<DeleteAccountForm email="jane@example.com" />);
    const button = screen.getByRole("button", { name: "Delete my account" });

    expect(button).toBeDisabled();
    type("jane@exmaple.com");
    expect(button).toBeDisabled();
    type(" Jane@Example.com ");
    expect(button).toBeEnabled();
  });

  it("deletes and leaves the signed-in screens", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetch);
    render(<DeleteAccountForm email="jane@example.com" />);

    type("jane@example.com");
    fireEvent.click(screen.getByRole("button", { name: "Delete my account" }));

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/signup"));
    expect(fetch.mock.calls[0][0]).toBe("/v1/account");
    expect(fetch.mock.calls[0][1].method).toBe("DELETE");
  });

  it("shows why a deletion was refused", async () => {
    const error = {
      error: {
        code: "confirmation_mismatch",
        message: "Type your email exactly.",
      },
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify(error), { status: 422 }),
        ),
    );
    render(<DeleteAccountForm email="jane@example.com" />);

    type("jane@example.com");
    fireEvent.click(screen.getByRole("button", { name: "Delete my account" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Type your email exactly.",
    );
    expect(router.replace).not.toHaveBeenCalled();
  });
});

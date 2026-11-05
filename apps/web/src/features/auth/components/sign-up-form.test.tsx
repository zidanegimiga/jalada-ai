import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SignUpForm } from "./sign-up-form";

const router = { replace: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Jane" } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "jane@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct horse battery" } });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
}

describe("SignUpForm", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("creates the account with the API's field names, then goes home", async () => {
    const body = JSON.stringify({ id: "1", email: "jane@example.com", display_name: "Jane" });
    const fetch = vi.fn().mockResolvedValue(new Response(body, { status: 201 }));
    vi.stubGlobal("fetch", fetch);
    render(<SignUpForm />);

    fillAndSubmit();

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/"));
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      email: "jane@example.com",
      password: "correct horse battery",
      display_name: "Jane",
    });
  });

  it("asks for at least 10 characters in the password field", () => {
    render(<SignUpForm />);

    expect(screen.getByLabelText("Password")).toHaveAttribute("minlength", "10");
    expect(screen.getByLabelText("Password")).toHaveAccessibleDescription("At least 10 characters.");
  });

  it("shows a taken email as an error", async () => {
    const error = { error: { code: "email_taken", message: "An account with this email already exists." } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(error), { status: 409 })));
    render(<SignUpForm />);

    fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent("already exists");
  });
});

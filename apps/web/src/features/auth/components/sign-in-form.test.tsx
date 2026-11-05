import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SignInForm } from "./sign-in-form";

const router = { replace: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "jane@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct horse" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

describe("SignInForm", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("sends the email and password, then goes home", async () => {
    const fetch = respond(200, { id: "1", email: "jane@example.com", display_name: "Jane" });
    vi.stubGlobal("fetch", fetch);
    render(<SignInForm />);

    fillAndSubmit();

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/"));
    const [path, init] = fetch.mock.calls[0];
    expect(path).toBe("/v1/auth/login");
    expect(JSON.parse(init.body)).toEqual({ email: "jane@example.com", password: "correct horse" });
  });

  it("shows the message from the API when sign-in fails", async () => {
    const message = "The email or password is wrong.";
    vi.stubGlobal("fetch", respond(401, { error: { code: "invalid_credentials", message } }));
    render(<SignInForm />);

    fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(router.replace).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });
});

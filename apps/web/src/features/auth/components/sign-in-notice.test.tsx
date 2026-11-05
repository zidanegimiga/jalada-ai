import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SignInNotice } from "./sign-in-notice";

let query = "";
vi.mock("next/navigation", () => ({ useSearchParams: () => new URLSearchParams(query) }));

describe("SignInNotice", () => {
  it("explains a failed Google sign-in", () => {
    query = "error=google_failed";
    render(<SignInNotice />);

    expect(screen.getByRole("alert")).toHaveTextContent("Google sign-in did not work");
  });

  it("shows nothing for an unknown or missing error", () => {
    query = "error=<script>";
    const { container } = render(<SignInNotice />);

    expect(container).toBeEmptyDOMElement();
  });
});

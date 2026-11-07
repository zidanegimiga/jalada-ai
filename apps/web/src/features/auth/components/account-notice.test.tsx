import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountNotice } from "./account-notice";

let query = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(query),
}));

describe("AccountNotice", () => {
  it("explains why the password was removed", () => {
    query = "notice=password_removed";
    render(<AccountNotice />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "This account's password was removed",
    );
  });

  it("shows nothing for an unknown notice", () => {
    query = "notice=anything";
    const { container } = render(<AccountNotice />);

    expect(container).toBeEmptyDOMElement();
  });
});

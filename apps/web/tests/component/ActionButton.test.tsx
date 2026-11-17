import { render, screen } from "@testing-library/react";
import { Download } from "lucide-react";
import { describe, expect, it } from "vitest";

import { ActionButton, ActionLink } from "@/shared/components/ActionButton";

describe("ActionButton", () => {
  it("is named by its label alone, the tile being decoration", () => {
    render(<ActionButton>Sign in</ActionButton>);

    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });

  it("cannot be pressed again while busy", () => {
    render(<ActionButton busy>Signing in...</ActionButton>);

    const button = screen.getByRole("button", { name: "Signing in..." });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });
});

describe("ActionLink", () => {
  it("is a link with the same look", () => {
    render(
      <ActionLink href="/v1/exports/2025.xlsx" download icon={Download}>
        Download 2025 (Excel)
      </ActionLink>,
    );

    expect(
      screen.getByRole("link", { name: "Download 2025 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2025.xlsx");
  });
});

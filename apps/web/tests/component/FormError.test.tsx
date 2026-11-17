import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormError } from "@/shared/components/FormError";

describe("FormError", () => {
  it("keeps an empty alert on the page before there is an error", () => {
    render(<FormError message={null} />);

    expect(screen.getByRole("alert")).toBeEmptyDOMElement();
  });

  it("shows the error in the same alert", () => {
    const { rerender } = render(<FormError message={null} />);
    const alert = screen.getByRole("alert");

    rerender(<FormError message="That did not work. Try again." />);

    expect(screen.getByRole("alert")).toBe(alert);
    expect(alert).toHaveTextContent("That did not work. Try again.");
  });
});

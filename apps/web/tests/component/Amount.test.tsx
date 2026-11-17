import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Amount } from "@/shared/components/Amount";

describe("Amount", () => {
  it("shows shillings with figures that line up", () => {
    render(<Amount cents={125000} />);

    expect(screen.getByText("KSh 1,250.00")).toHaveClass("tabular-nums");
  });
});

describe("Amount with faded cents", () => {
  it("is still read as one plain amount", () => {
    render(<Amount cents={125050} fadeCents />);

    expect(screen.getByText("KSh 1,250.50")).toHaveClass("sr-only");
    expect(screen.getByText(".50")).toHaveClass("opacity-45");
  });
});

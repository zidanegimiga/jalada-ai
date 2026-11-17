import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChipTabs } from "@/shared/components/ChipTabs";

const CHIPS = [
  { value: "", label: "All" },
  { value: "in", label: "Money in" },
];

describe("ChipTabs", () => {
  it("marks the chosen chip and reports a new choice", () => {
    const onChange = vi.fn();
    render(
      <ChipTabs label="Direction" chips={CHIPS} value="" onChange={onChange} />,
    );

    expect(
      screen.getByRole("group", { name: "Direction" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    fireEvent.click(screen.getByRole("button", { name: "Money in" }));
    expect(onChange).toHaveBeenCalledWith("in");
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MonthPicker } from "@/shared/components/MonthPicker";

describe("MonthPicker", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 10, 17));
  });

  afterEach(() => vi.useRealTimers());

  it("names the picked month, or says all months", () => {
    const { rerender } = render(
      <MonthPicker label="Month" value="" onChange={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: "Month" })).toHaveTextContent(
      "All months",
    );

    rerender(<MonthPicker label="Month" value="2026-03" onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Month" })).toHaveTextContent(
      "March 2026",
    );
  });

  it("picks a month from an earlier year, never a future one", async () => {
    const onChange = vi.fn();
    render(<MonthPicker label="Month" value="" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Month" }));
    expect(
      await screen.findByRole("button", { name: "December 2026" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next year" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Previous year" }));
    fireEvent.click(screen.getByRole("button", { name: "July 2025" }));

    expect(onChange).toHaveBeenCalledWith("2025-07");
  });

  it("clears back to all months", async () => {
    const onChange = vi.fn();
    render(<MonthPicker label="Month" value="2026-03" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Month" }));
    expect(
      await screen.findByRole("button", { name: "March 2026" }),
    ).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "All months" }));

    expect(onChange).toHaveBeenCalledWith("");
  });
});

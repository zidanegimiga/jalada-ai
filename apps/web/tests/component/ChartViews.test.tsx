import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BalanceLine, runningNet } from "@/shared/components/BalanceLine";
import { CategoryWaffle, squares } from "@/shared/components/CategoryWaffle";
import { ChartViews } from "@/shared/components/ChartViews";
import { MoneyFlow } from "@/shared/components/MoneyFlow";
import { PurposeColumns } from "@/shared/components/PurposeColumns";
import { YearWheel } from "@/shared/components/YearWheel";

function month(
  key: string,
  label: string,
  [inCents, outCents, inBusinessCents, outBusinessCents]: number[],
) {
  return {
    key,
    label,
    short: label.slice(0, 3),
    inCents,
    outCents,
    inBusinessCents,
    outBusinessCents,
  };
}

// Invented months, in cents.
const MONTHS = [
  month("2026-01", "January 2026", [100_000, 60_000, 80_000, 10_000]),
  month("2026-02", "February 2026", [20_000, 90_000, 0, 30_000]),
  month("2026-03", "March 2026", [0, 0, 0, 0]),
];

const SLICES = {
  in: [
    { name: "Client payments", cents: 300_000 },
    { name: "Salary", cents: 100_000 },
  ],
  out: [
    { name: "Rent", cents: 150_000 },
    { name: "Food", cents: 50_000 },
  ],
};

describe("chart views", () => {
  it("shows one view at a time and switches on a chip", () => {
    render(
      <ChartViews
        label="Show as"
        views={[
          { value: "a", label: "First", content: <p>First view</p> },
          { value: "b", label: "Second", content: <p>Second view</p> },
        ]}
      />,
    );
    expect(screen.getByText("First view")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Second" }));

    expect(screen.getByText("Second view")).toBeInTheDocument();
    expect(screen.queryByText("First view")).not.toBeInTheDocument();
  });

  it("adds up what was kept month by month, up to now", () => {
    expect(runningNet(MONTHS, 1)).toEqual([40_000, -30_000]);
  });

  it("reads out what was kept each month", () => {
    render(<BalanceLine points={MONTHS} current={1} />);

    expect(screen.getByRole("img")).toHaveAccessibleName(
      /^Money kept.*Jan.*Feb/,
    );
  });

  it("says how much of each month was business", () => {
    render(<PurposeColumns points={MONTHS} />);

    expect(screen.getByRole("img")).toHaveAccessibleName(
      /January 2026: in KSh 1,000.*KSh 800.* of it business/,
    );
  });

  it("draws every month around the wheel", () => {
    const { container } = render(<YearWheel points={MONTHS} />);

    expect(container.querySelectorAll(".wheel-month")).toHaveLength(3);
  });

  it("always fills exactly 100 squares", () => {
    const thirds = [1, 1, 1].map((cents, index) => ({
      name: `${index}`,
      cents,
    }));

    expect(squares(thirds)).toEqual([34, 33, 33]);
    expect(squares([])).toEqual([]);
  });

  it("shows money in and out as squares with their names", () => {
    render(<CategoryWaffle slices={SLICES} />);

    expect(screen.getAllByRole("img")).toHaveLength(2);
    expect(screen.getByText("Rent")).toBeInTheDocument();
    expect(screen.getByText("Client payments")).toBeInTheDocument();
  });

  it("draws a band for every category, in and out", () => {
    const { container } = render(<MoneyFlow slices={SLICES} />);

    expect(container.querySelectorAll(".flow-band")).toHaveLength(4);
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /Money in: Client payments/,
    );
  });

  it("says so when there is nothing to draw", () => {
    render(<MoneyFlow slices={{ in: [], out: [] }} />);

    expect(screen.getByText(/Nothing confirmed yet/)).toBeInTheDocument();
  });
});

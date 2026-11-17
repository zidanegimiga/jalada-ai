import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CategoryBreakdown } from "@/shared/components/CategoryBreakdown";
import { InOutChart } from "@/shared/components/InOutChart";

const POINTS = [
  {
    key: "2026-10",
    label: "October 2026",
    short: "Oct",
    inCents: 500000,
    outCents: 20000,
  },
  {
    key: "2026-11",
    label: "November 2026",
    short: "Nov",
    inCents: 0,
    outCents: 15000,
  },
];

describe("InOutChart", () => {
  it("names every month with its amounts and reads out the one chosen", () => {
    render(<InOutChart points={POINTS} />);

    expect(screen.getByText("November 2026")).toBeInTheDocument();
    const october = screen.getByRole("button", {
      name: "October 2026: in KSh 5,000.00, out KSh 200.00",
    });

    fireEvent.click(october);

    expect(october).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("October 2026")).toBeInTheDocument();
    expect(screen.getByText("KSh 5,000.00")).toBeInTheDocument();
  });
});

describe("CategoryBreakdown", () => {
  it("shows money out first, with each share, and switches to money in", () => {
    render(
      <CategoryBreakdown
        slices={{
          out: [
            { name: "Food", cents: 7500 },
            { name: "Transport", cents: 2500 },
          ],
          in: [],
        }}
      />,
    );

    expect(screen.getByText("Food")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Money in" }));

    expect(
      screen.getByText("Nothing confirmed coming in yet."),
    ).toBeInTheDocument();
  });
});

describe("InOutChart for a year still running", () => {
  it("opens on this month and holds back the months to come", () => {
    render(<InOutChart points={POINTS} current={0} />);

    expect(
      screen.getByRole("button", { name: /^October 2026/ }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: /^November 2026/ }),
    ).toBeDisabled();
  });
});

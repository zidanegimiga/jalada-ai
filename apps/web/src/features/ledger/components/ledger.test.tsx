import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { entry } from "@/features/review/components/test-data";

import { LedgerFilters } from "./ledger-filters";
import { LedgerList } from "./ledger-list";
import { MonthCard } from "./month-card";

const router = { replace: vi.fn() };
let query = "";
vi.mock("next/navigation", () => ({
  useRouter: () => router,
  usePathname: () => "/ledger",
  useSearchParams: () => new URLSearchParams(query),
}));

describe("LedgerList", () => {
  it("marks money in and money out", () => {
    render(
      <LedgerList
        entries={[
          entry({
            id: "a",
            direction: "in",
            amount_cents: 4_000_000,
            counterparty: "CLIENT",
            category_name: "Consultancy",
          }),
          entry({ id: "b", direction: "out", amount_cents: 15000 }),
        ]}
      />,
    );

    expect(screen.getByText("+KSh 40,000.00")).toHaveClass("text-money-in");
    expect(screen.getByText("−KSh 150.00")).not.toHaveClass("text-money-in");
    expect(screen.getByText("Consultancy · 4 Nov 2026")).toBeInTheDocument();
  });
});

describe("MonthCard", () => {
  it("totals money in and out and splits them by purpose", () => {
    render(
      <MonthCard
        year={2026}
        month={{
          month: 11,
          in_business_cents: 4_000_000,
          in_personal_cents: 500_000,
          out_business_cents: 25_000,
          out_personal_cents: 0,
        }}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "November 2026" }),
    ).toBeInTheDocument();
    expect(screen.getByText("KSh 45,000.00")).toBeInTheDocument();
    expect(
      screen.getByText("Business KSh 40,000.00 · Personal KSh 5,000.00"),
    ).toBeInTheDocument();
  });
});

describe("LedgerFilters", () => {
  it("keeps filters in the address and starts again from the first page", () => {
    query = "month=2026-11&cursor=abc";
    render(<LedgerFilters />);

    fireEvent.click(screen.getByRole("button", { name: "Business" }));

    expect(router.replace).toHaveBeenCalledWith(
      "/ledger?month=2026-11&purpose=business",
    );
    expect(screen.getByRole("button", { name: "Money in" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });
});

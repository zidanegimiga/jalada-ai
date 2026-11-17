import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { entry } from "../support/review-fixtures";

import { LedgerFilters } from "@/features/ledger/components/LedgerFilters";
import { LedgerList } from "@/features/ledger/components/LedgerList";
import { MonthCard } from "@/features/ledger/components/MonthCard";

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
            category_suggested: false,
          }),
          entry({ id: "b", direction: "out", amount_cents: 15000 }),
        ]}
      />,
    );

    expect(screen.getByText("+KSh 40,000.00")).toHaveClass("text-money-in");
    expect(screen.getByText("−KSh 150.00")).not.toHaveClass("text-money-in");
    expect(screen.getByText("Consultancy · 4 Nov 2026")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "November 2026" }),
    ).toBeInTheDocument();
  });
});

describe("LedgerList with a search", () => {
  it("marks the searched words in each name", () => {
    render(
      <LedgerList
        entries={[entry({ id: "s", counterparty: "MAMA MBOGA SHOP" })]}
        filtered
        search="mboga"
      />,
    );

    expect(screen.getByText("MBOGA").tagName).toBe("MARK");
  });

  it("says which words found nothing", () => {
    render(<LedgerList entries={[]} filtered search="otieno" />);

    expect(
      screen.getByText("No confirmed entries with “otieno” fit these filters."),
    ).toBeInTheDocument();
  });
});

describe("LedgerList with transfers", () => {
  it("mutes a move between own accounts and says it is not counted", () => {
    render(
      <LedgerList
        entries={[
          entry({
            id: "t",
            direction: "out",
            amount_cents: 145000,
            counterparty: "SAMPLE BANK",
            category: "own_transfer_out",
            category_name: "Transfer to own account",
            category_suggested: false,
          }),
        ]}
      />,
    );

    expect(screen.getByText("KSh 1,450.00")).toHaveClass(
      "text-muted-foreground",
    );
    expect(screen.queryByText("−KSh 1,450.00")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Transfer to own account · 4 Nov 2026 · Not counted in totals",
      ),
    ).toBeInTheDocument();
  });
});

describe("LedgerList with certificates", () => {
  it("links certificates to their page and marks payments counted through them", () => {
    render(
      <LedgerList
        entries={[
          entry({
            id: "cert-1",
            kind: "withholding_certificate",
            direction: "in",
            amount_cents: 4_000_000,
            counterparty: "CLIENT",
            category_name: "Consultancy",
            category_suggested: false,
            linked_payment_ids: ["pay-1"],
          }),
          entry({
            id: "pay-1",
            direction: "in",
            amount_cents: 3_800_000,
            counterparty: "CLIENT",
            category_name: "Consultancy",
            category_suggested: false,
            linked_certificate_id: "cert-1",
          }),
        ]}
      />,
    );

    expect(
      screen.getAllByRole("link").map((link) => link.getAttribute("href")),
    ).toEqual(["/ledger/certificates/cert-1", "/ledger/entries/pay-1"]);
    expect(
      screen.getByText(
        "Withholding certificate · 4 Nov 2026 · 1 payment linked",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Consultancy · 4 Nov 2026 · Counted on its certificate"),
    ).toBeInTheDocument();
    expect(screen.getByText("+KSh 38,000.00")).not.toHaveClass("text-money-in");
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

  it("clears every filter at once, and offers to only when something is filtered", () => {
    query = "month=2026-11&direction=in&purpose=business";
    const { unmount } = render(<LedgerFilters />);

    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(router.replace).toHaveBeenLastCalledWith("/ledger");
    unmount();

    query = "";
    render(<LedgerFilters />);
    expect(
      screen.queryByRole("button", { name: "Clear filters" }),
    ).not.toBeInTheDocument();
  });

  it("points a new user to To check when the ledger is empty", () => {
    render(<LedgerList entries={[]} />);

    expect(screen.getByText("Your ledger is empty")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Go to To check" }),
    ).toHaveAttribute("href", "/review");
  });

  it("offers to clear the filters when nothing matches them", () => {
    render(<LedgerList entries={[]} filtered />);

    expect(screen.getByText("Nothing matches")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Show everything" }),
    ).toHaveAttribute("href", "/ledger");
  });
});

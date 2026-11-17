import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReviewList } from "@/features/review/components/ReviewList";
import { CATEGORIES, entry, item, matchItem } from "../support/review-fixtures";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

function ready(id: string, counterparty: string) {
  return { ...item(entry({ id, counterparty })), ready: true };
}

describe("ReviewList", () => {
  it("asks questions first, then lists what is ready under Confirm all", () => {
    render(
      <ReviewList
        items={[
          ready("a", "JANE WANJIKU"),
          matchItem(),
          ready("b", "SAMPLE SHOP"),
        ]}
        categories={CATEGORIES}
      />,
    );

    const section = screen.getByRole("region", { name: "Ready to confirm" });
    expect(
      within(section).getByText("JANE WANJIKU · 4 Nov 2026"),
    ).toBeInTheDocument();
    expect(
      within(section).getByText("SAMPLE SHOP · 4 Nov 2026"),
    ).toBeInTheDocument();
    expect(
      within(section).getByRole("button", { name: "Confirm all 2" }),
    ).toBeInTheDocument();
    const question = screen.getByText(/SAMPLE MUSIC SHOP/);
    expect(section).not.toContainElement(question);
  });

  it("leaves out Confirm all for a single ready payment", () => {
    render(
      <ReviewList
        items={[ready("a", "JANE WANJIKU")]}
        categories={CATEGORIES}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Ready to confirm" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Confirm all/ })).toBeNull();
  });
});

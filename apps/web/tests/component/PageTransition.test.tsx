import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PageTransition } from "@/app/(app)/_components/PageTransition";

vi.mock("next/navigation", () => ({ usePathname: () => "/ledger" }));

describe("PageTransition", () => {
  it("shows the page inside it", () => {
    render(
      <PageTransition>
        <h1>Ledger</h1>
      </PageTransition>,
    );

    expect(screen.getByRole("heading", { name: "Ledger" })).toBeInTheDocument();
  });
});

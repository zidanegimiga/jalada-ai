import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppNav } from "@/app/(app)/_components/AppNav";
import { destinations } from "@/app/(app)/_components/navigation";

const path = vi.hoisted(() => ({ current: "/review" }));
vi.mock("next/navigation", () => ({ usePathname: () => path.current }));

describe("AppNav", () => {
  it("links the three screens and marks the current one", () => {
    render(<AppNav />);

    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("link", { name: "Ledger" })).toHaveAttribute(
      "href",
      "/ledger",
    );
    expect(screen.getByRole("link", { name: "To check" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("keeps the ledger marked on a page inside it", () => {
    path.current = "/ledger/certificates/1";
    render(<AppNav />);

    expect(screen.getByRole("link", { name: "Ledger" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    path.current = "/review";
  });

  it("adds Ask only where the assistant is switched on", () => {
    expect(destinations("off").map((d) => d.label)).toEqual([
      "Home",
      "To check",
      "Ledger",
    ]);
    path.current = "/ask";
    render(<AppNav places={destinations("on")} />);

    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    path.current = "/review";
  });

  it("puts the badge on To check", () => {
    render(<AppNav toCheck={<span>, 3 waiting</span>} />);

    expect(
      screen.getByRole("link", { name: /^To check.*3 waiting$/ }),
    ).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Spinner } from "./spinner";

describe("Spinner", () => {
  it("tells screen readers that content is loading", () => {
    render(<Spinner />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading");
  });

  it("can name what is loading", () => {
    render(<Spinner label="Loading your ledger" />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading your ledger");
  });

  it("spins only when the user allows motion", () => {
    const { container } = render(<Spinner />);

    expect(container.querySelector("svg")).toHaveClass(
      "motion-safe:animate-spin",
    );
  });
});

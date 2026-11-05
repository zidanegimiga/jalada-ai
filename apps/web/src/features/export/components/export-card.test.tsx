import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExportCard } from "./export-card";

describe("ExportCard", () => {
  it("offers last year first, because that is the return being filed", () => {
    render(<ExportCard currentYear={2026} />);

    expect(screen.getByLabelText("Year")).toHaveValue("2025");
    expect(
      screen.getByRole("link", { name: "Download 2025 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2025.xlsx");
  });

  it("downloads the chosen year", () => {
    render(<ExportCard currentYear={2026} />);

    fireEvent.change(screen.getByLabelText("Year"), {
      target: { value: "2026" },
    });

    expect(
      screen.getByRole("link", { name: "Download 2026 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2026.xlsx");
  });
});

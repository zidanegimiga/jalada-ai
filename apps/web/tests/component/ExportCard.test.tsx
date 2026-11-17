import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExportCard } from "@/features/export/components/ExportCard";

describe("ExportCard", () => {
  it("offers the default year first", () => {
    render(<ExportCard currentYear={2026} defaultYear={2025} />);

    expect(screen.getByLabelText("Year")).toHaveValue("2025");
    expect(
      screen.getByRole("link", { name: "Download 2025 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2025.xlsx");
  });

  it("downloads the chosen year", () => {
    render(<ExportCard currentYear={2026} defaultYear={2025} />);

    fireEvent.change(screen.getByLabelText("Year"), {
      target: { value: "2026" },
    });

    expect(
      screen.getByRole("link", { name: "Download 2026 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2026.xlsx");
  });
});

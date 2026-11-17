import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExportCard } from "@/features/export/components/ExportCard";

import { chooseOption } from "../support/choose";

describe("ExportCard", () => {
  it("offers the default year first", () => {
    render(<ExportCard currentYear={2026} defaultYear={2025} />);

    expect(screen.getByRole("combobox", { name: "Year" })).toHaveTextContent(
      "2025",
    );
    expect(
      screen.getByRole("link", { name: "Download 2025 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2025.xlsx");
  });

  it("downloads the chosen year", async () => {
    render(<ExportCard currentYear={2026} defaultYear={2025} />);

    await chooseOption("Year", "2026");

    expect(
      screen.getByRole("link", { name: "Download 2026 (Excel)" }),
    ).toHaveAttribute("href", "/v1/exports/2026.xlsx");
  });
});

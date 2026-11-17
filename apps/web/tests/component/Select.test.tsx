import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Select } from "@/shared/components/Select";

import { chooseOption } from "../support/choose";

const YEARS = [
  { value: "2026", label: "2026" },
  { value: "2025", label: "2025" },
];

describe("Select", () => {
  it("is named by its label and shows the chosen option", () => {
    render(<Select label="Year" options={YEARS} value="2025" />);

    expect(screen.getByRole("combobox", { name: "Year" })).toHaveTextContent(
      "2025",
    );
  });

  it("reports the option picked from the list", async () => {
    const onValueChange = vi.fn();
    render(
      <Select
        label="Year"
        options={YEARS}
        value="2025"
        onValueChange={onValueChange}
      />,
    );

    await chooseOption("Year", "2026");

    expect(onValueChange).toHaveBeenCalledWith("2026");
  });

  it("sends its value with the form, like a native select", () => {
    const { container } = render(
      <form>
        <Select label="Year" options={YEARS} defaultValue="2026" name="year" />
      </form>,
    );

    const form = container.querySelector("form")!;
    expect(new FormData(form).get("year")).toBe("2026");
  });
});

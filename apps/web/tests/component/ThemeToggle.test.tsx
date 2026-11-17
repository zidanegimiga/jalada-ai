import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "@/shared/components/ThemeToggle";

const root = document.documentElement;

function phoneIsDark(dark: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: dark && query.includes("dark"),
  }));
}

describe("ThemeToggle", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    delete root.dataset.theme;
  });

  it("switches to the opposite of what the phone shows", () => {
    phoneIsDark(true);
    render(<ThemeToggle />);

    fireEvent.click(
      screen.getByRole("button", { name: "Switch between light and dark" }),
    );

    expect(root.dataset.theme).toBe("light");
  });

  it("switches back from a picked theme", () => {
    phoneIsDark(false);
    root.dataset.theme = "dark";
    render(<ThemeToggle />);

    fireEvent.click(
      screen.getByRole("button", { name: "Switch between light and dark" }),
    );

    expect(root.dataset.theme).toBe("light");
  });
});

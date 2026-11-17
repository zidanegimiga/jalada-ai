import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeChoice } from "@/shared/components/ThemeChoice";
import { THEME_STORAGE_KEY } from "@/shared/theme/theme";

const root = document.documentElement;

describe("ThemeChoice", () => {
  beforeEach(() => {
    vi.stubGlobal("matchMedia", () => ({ matches: false }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    delete root.dataset.theme;
  });

  it("follows the phone until something is picked", () => {
    render(<ThemeChoice />);

    expect(screen.getByLabelText("Auto")).toBeChecked();
    expect(root.dataset.theme).toBeUndefined();
  });

  it("applies and remembers a picked theme", () => {
    render(<ThemeChoice />);

    fireEvent.click(screen.getByLabelText("Dark"));

    expect(root.dataset.theme).toBe("dark");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
  });

  it("goes back to following the phone", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "light");
    root.dataset.theme = "light";
    render(<ThemeChoice />);
    expect(screen.getByLabelText("Light")).toBeChecked();

    fireEvent.click(screen.getByLabelText("Auto"));

    expect(root.dataset.theme).toBeUndefined();
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBeNull();
  });
});

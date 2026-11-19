import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Reading } from "@/features/landing/components/Reading";

function prefersStill(still: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: still && query.includes("reduce"),
  }));
}

/** The part of the message lit up as the source of the chosen field. */
const lit = () =>
  Array.from(document.querySelectorAll("mark"))
    .filter((mark) => mark.dataset.on === "true")
    .map((mark) => mark.textContent);

describe("Reading", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("lights up where a field came from in the message", () => {
    prefersStill(true);
    render(<Reading />);

    fireEvent.click(screen.getByRole("button", { name: /Paid to/ }));

    expect(lit()).toEqual(["NAIVAS WESTGATE"]);
    expect(screen.getByRole("button", { name: /Paid to/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("takes the fields in turn when left alone", () => {
    prefersStill(false);
    render(<Reading />);
    expect(lit()).toEqual(["Ksh2,450.00"]);

    act(() => vi.advanceTimersByTime(2200));

    expect(lit()).toEqual(["NAIVAS WESTGATE"]);
  });

  it("stays still for people who ask for less motion", () => {
    prefersStill(true);
    render(<Reading />);

    act(() => vi.advanceTimersByTime(10_000));

    expect(lit()).toEqual(["Ksh2,450.00"]);
  });
});

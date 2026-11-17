import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DatePicker } from "@/shared/components/DatePicker";

function form() {
  return render(
    <form>
      <DatePicker label="Date" name="occurred_on" defaultValue="2026-11-04" />
    </form>,
  );
}

const sent = (container: HTMLElement) =>
  new FormData(container.querySelector("form")!).get("occurred_on");

describe("DatePicker", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 10, 17));
  });

  afterEach(() => vi.useRealTimers());

  it("shows the date and sends it with the form", () => {
    const { container } = form();

    expect(screen.getByRole("button", { name: "Date" })).toHaveTextContent(
      "4 Nov 2026",
    );
    expect(sent(container)).toBe("2026-11-04");
  });

  it("picks a day from the calendar, never one after today", async () => {
    const { container } = form();

    fireEvent.click(screen.getByRole("button", { name: "Date" }));
    expect(
      await screen.findByRole("button", { name: /18 November 2026/ }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next month" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Previous month" }));
    fireEvent.click(screen.getByRole("button", { name: /31 October 2026/ }));

    expect(sent(container)).toBe("2026-10-31");
    expect(screen.getByRole("button", { name: "Date" })).toHaveTextContent(
      "31 Oct 2026",
    );
  });
});

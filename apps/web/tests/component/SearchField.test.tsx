import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SearchField } from "@/shared/components/SearchField";

function field(value = "", onSearch = vi.fn()) {
  return render(
    <SearchField
      label="Search the ledger"
      placeholder="Search"
      value={value}
      onSearch={onSearch}
    />,
  );
}

describe("SearchField", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("searches once typing pauses, not on every key", () => {
    const onSearch = vi.fn();
    field("", onSearch);
    const box = screen.getByRole("searchbox", { name: "Search the ledger" });

    fireEvent.change(box, { target: { value: "mb" } });
    fireEvent.change(box, { target: { value: "mboga " } });
    act(() => vi.advanceTimersByTime(299));
    expect(onSearch).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(1));
    expect(onSearch).toHaveBeenCalledExactlyOnceWith("mboga");
  });

  it("clears at once with its button", () => {
    const onSearch = vi.fn();
    field("mboga", onSearch);

    fireEvent.click(screen.getByRole("button", { name: "Clear the search" }));

    expect(onSearch).toHaveBeenCalledWith("");
    expect(screen.getByRole("searchbox")).toHaveValue("");
  });

  it("shows a search changed from outside, such as Clear filters", () => {
    const { rerender } = field("mboga");

    rerender(
      <SearchField
        label="Search the ledger"
        placeholder="Search"
        value=""
        onSearch={vi.fn()}
      />,
    );

    expect(screen.getByRole("searchbox")).toHaveValue("");
  });
});

import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  AuthHandoff,
  HANDOFF_MS,
  HandoffLink,
} from "@/features/auth/components/Handoff";

const push = vi.hoisted(() => vi.fn());
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

function stillMotion(still: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: still && query.includes("reduce"),
  }));
}

function page() {
  return render(
    <AuthHandoff>
      <HandoffLink href="/signup" destination="Create account">
        Create an account
      </HandoffLink>
    </AuthHandoff>,
  );
}

const cover = () => document.querySelector("[data-phase]");

describe("Handoff", () => {
  beforeEach(() => vi.useFakeTimers());

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    push.mockReset();
  });

  it("covers the page, changes it underneath, then lifts away", () => {
    stillMotion(false);
    page();

    fireEvent.click(screen.getByRole("link", { name: "Create an account" }));
    expect(cover()).toHaveAttribute("data-phase", "covering");
    expect(cover()).toHaveTextContent("Create account");
    expect(push).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(HANDOFF_MS.cover));
    expect(push).toHaveBeenCalledWith("/signup");

    act(() => vi.advanceTimersByTime(HANDOFF_MS.hold));
    expect(cover()).toHaveAttribute("data-phase", "revealing");

    act(() => vi.advanceTimersByTime(HANDOFF_MS.reveal));
    expect(cover()).toBeNull();
  });

  it("goes straight there for people who ask for less motion", () => {
    stillMotion(true);
    page();

    fireEvent.click(screen.getByRole("link", { name: "Create an account" }));

    expect(push).toHaveBeenCalledWith("/signup");
    expect(cover()).toBeNull();
  });

  it("leaves a new-tab click to the browser", () => {
    stillMotion(false);
    page();

    fireEvent.click(screen.getByRole("link", { name: "Create an account" }), {
      metaKey: true,
    });

    expect(push).not.toHaveBeenCalled();
    expect(cover()).toBeNull();
  });
});

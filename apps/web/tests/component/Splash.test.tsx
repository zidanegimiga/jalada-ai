import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SPLASH } from "@/app/_components/Splash/splash-config";
import { Splash } from "@/app/_components/Splash";

function prefersStill(still: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: still && query.includes("reduce"),
  }));
}

const splash = () => document.getElementById("splash") as HTMLElement;
const root = document.documentElement;

describe("Splash", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(performance, "now").mockReturnValue(0);
    prefersStill(false);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    sessionStorage.clear();
    delete root.dataset.splash;
  });

  it("stays until the opening has played, then plays out and hides", () => {
    render(<Splash />);
    expect(splash().dataset.state).toBeUndefined();

    act(() => vi.advanceTimersByTime(SPLASH.minimumMs));
    expect(splash().dataset.state).toBe("leaving");
    expect(sessionStorage.getItem(SPLASH.storageKey)).toBe("1");

    act(() => {
      splash().dispatchEvent(new Event("animationend", { bubbles: true }));
    });
    expect(root.dataset.splash).toBe("seen");
  });

  it("ignores animations ending inside it", () => {
    render(<Splash />);
    act(() => vi.advanceTimersByTime(SPLASH.minimumMs));

    act(() => {
      splash()
        .querySelector("span")!
        .dispatchEvent(new Event("animationend", { bubbles: true }));
    });
    expect(root.dataset.splash).toBeUndefined();
  });

  it("hides at once for people who ask for less motion", () => {
    prefersStill(true);
    render(<Splash />);

    act(() => vi.advanceTimersByTime(0));
    expect(root.dataset.splash).toBe("seen");
  });

  it("does nothing once it has been seen", () => {
    root.dataset.splash = "seen";
    render(<Splash />);

    act(() => vi.advanceTimersByTime(SPLASH.minimumMs));
    expect(splash().dataset.state).toBeUndefined();
  });
});

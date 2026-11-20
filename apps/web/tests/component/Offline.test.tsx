import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConnectionStatus } from "@/features/offline/components/ConnectionStatus";
import { ServiceWorkerSetup } from "@/features/offline/components/ServiceWorkerSetup";
import { ACTIVATE_UPDATE } from "@/features/offline/service-worker";

function goOffline(offline: boolean) {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(!offline);
  act(() => {
    window.dispatchEvent(new Event(offline ? "offline" : "online"));
  });
}

/** A service worker registration whose new version has already downloaded. */
function updateWaiting() {
  const waiting = { postMessage: vi.fn() };
  const register = vi.fn().mockResolvedValue({
    waiting,
    addEventListener: vi.fn(),
  });
  Object.defineProperty(navigator, "serviceWorker", {
    configurable: true,
    value: {
      register,
      controller: {},
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    },
  });
  return { register, waiting };
}

describe("offline", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    Reflect.deleteProperty(navigator, "serviceWorker");
  });

  it("says what still works while offline, and when the connection is back", () => {
    vi.useFakeTimers();
    render(<ConnectionStatus />);
    expect(screen.queryByText(/offline/)).not.toBeInTheDocument();

    goOffline(true);
    expect(screen.getByText(/You are offline/)).toBeInTheDocument();

    goOffline(false);
    act(() => vi.advanceTimersByTime(10));
    expect(screen.getByText("Back online.")).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(3000));
    expect(screen.queryByText("Back online.")).not.toBeInTheDocument();
  });

  it("does not register a service worker in development", () => {
    const { register } = updateWaiting();
    render(<ServiceWorkerSetup enabled={false} />);

    expect(register).not.toHaveBeenCalled();
  });

  it("offers to reload when a new version is ready, and only switches when asked", async () => {
    const { register, waiting } = updateWaiting();
    render(<ServiceWorkerSetup enabled />);

    expect(register).toHaveBeenCalledWith("/sw.js");
    const reload = await screen.findByRole("button", { name: "Reload" });
    expect(waiting.postMessage).not.toHaveBeenCalled();

    fireEvent.click(reload);
    expect(waiting.postMessage).toHaveBeenCalledWith(ACTIVATE_UPDATE);
  });
});

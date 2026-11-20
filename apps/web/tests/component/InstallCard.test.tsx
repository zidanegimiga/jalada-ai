import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { InstallCard } from "@/features/install/components/InstallCard";
import { catchInstallPrompt } from "@/features/install/install-prompt";

function standalone(on: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: on && query.includes("standalone"),
  }));
}

/** The browser offering to install, as Chrome does once the app qualifies. */
function offerInstall(outcome: "accepted" | "dismissed") {
  const offer = Object.assign(new Event("beforeinstallprompt"), {
    prompt: vi.fn().mockResolvedValue(undefined),
    userChoice: Promise.resolve({ outcome }),
  });
  act(() => {
    window.dispatchEvent(offer);
  });
  return offer;
}

describe("InstallCard", () => {
  let stop: () => void;
  beforeEach(() => {
    stop = catchInstallPrompt();
  });
  afterEach(() => {
    stop();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("offers the browser's own install question when there is one", async () => {
    standalone(false);
    render(<InstallCard />);
    const offer = offerInstall("accepted");

    fireEvent.click(screen.getByRole("button", { name: "Install Jalada AI" }));

    await vi.waitFor(() => expect(offer.prompt).toHaveBeenCalled());
  });

  it("explains Add to Home Screen on an iPhone, which has no install question", () => {
    standalone(false);
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue(
      "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) Safari",
    );
    render(<InstallCard />);

    expect(
      screen.getByText(/tap Share, then Add to Home Screen/),
    ).toBeInTheDocument();
  });

  it("says so when it is already installed", () => {
    standalone(true);
    render(<InstallCard />);

    expect(screen.getByText(/installed on this device/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

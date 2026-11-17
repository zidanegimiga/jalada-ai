import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ClickSounds } from "@/app/_components/ClickSounds";
import { SoundChoice } from "@/shared/components/SoundChoice";
import { SOUND_STORAGE_KEY } from "@/shared/sound/sound-setting";

const playClick = vi.hoisted(() => vi.fn());
vi.mock("@/shared/sound/click", () => ({ playClick }));

function page() {
  return render(
    <>
      <ClickSounds />
      <button type="button">Confirm</button>
      <button type="button" disabled>
        Saving
      </button>
      <p>Plain text</p>
      <SoundChoice />
    </>,
  );
}

describe("ClickSounds", () => {
  afterEach(() => {
    playClick.mockClear();
    localStorage.clear();
  });

  it("taps when a button is pressed, not on text or a disabled button", () => {
    page();

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    fireEvent.click(screen.getByText("Plain text"));
    fireEvent.click(screen.getByRole("button", { name: "Saving" }));

    expect(playClick).toHaveBeenCalledTimes(1);
  });

  it("stays quiet once tap sounds are turned off", () => {
    page();
    const toggle = screen.getByRole("switch", { name: "Tap sounds" });
    expect(toggle).toHaveAttribute("aria-checked", "true");

    fireEvent.click(toggle);
    playClick.mockClear();
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    expect(toggle).toHaveAttribute("aria-checked", "false");
    expect(localStorage.getItem(SOUND_STORAGE_KEY)).toBe("off");
    expect(playClick).not.toHaveBeenCalled();
  });
});

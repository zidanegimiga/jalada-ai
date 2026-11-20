import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GoogleButton } from "@/features/auth/components/GoogleButton";
import { AuthHandoff, HandoffLink } from "@/features/auth/components/Handoff";
import { withReturnPath } from "@/features/auth/hooks/useReturnPath";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), prefetch: vi.fn() }),
}));

const DESKTOP = "/desktop/sign-in?challenge=abc&state=def";

/** Opens the page as the proxy sends someone to it: with where to go back to. */
function arriveWith(next: string | null) {
  const query = next ? `?next=${encodeURIComponent(next)}` : "";
  window.history.replaceState(null, "", `/signin${query}`);
}

describe("keeping the page to go back to", () => {
  afterEach(() => arriveWith(null));

  it("adds it to a link", () => {
    expect(withReturnPath("/signup", DESKTOP)).toBe(
      `/signup?next=${encodeURIComponent(DESKTOP)}`,
    );
    expect(withReturnPath("/signup", null)).toBe("/signup");
  });

  it("goes with Google sign-in", () => {
    arriveWith(DESKTOP);
    render(<GoogleButton />);

    const href = screen
      .getByRole("link", { name: /Continue with Google/ })
      .getAttribute("href");
    expect(href).toBe(
      `/v1/auth/google/start?next=${encodeURIComponent(DESKTOP)}`,
    );
  });

  it("goes along when switching to sign-up", () => {
    arriveWith(DESKTOP);
    render(
      <AuthHandoff>
        <HandoffLink href="/signup" destination="Create account">
          Create an account
        </HandoffLink>
      </AuthHandoff>,
    );

    expect(
      screen.getByRole("link", { name: "Create an account" }),
    ).toHaveAttribute("href", `/signup?next=${encodeURIComponent(DESKTOP)}`);
  });

  it("is dropped when it points anywhere but this site", () => {
    arriveWith("//evil.example/steal");
    render(<GoogleButton />);

    expect(
      screen.getByRole("link", { name: /Continue with Google/ }),
    ).toHaveAttribute("href", "/v1/auth/google/start");
  });
});

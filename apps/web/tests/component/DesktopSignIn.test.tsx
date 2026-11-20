import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DesktopSignIn } from "@/features/desktop/components/DesktopSignIn";
import { readDesktopRequest } from "@/features/desktop/desktop-sign-in";

const REQUEST = { challenge: "a".repeat(43), state: "b".repeat(32) };

describe("DesktopSignIn", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("only accepts a request shaped like the desktop app's", () => {
    expect(readDesktopRequest(REQUEST)).toEqual(REQUEST);
    expect(
      readDesktopRequest({ challenge: "short", state: REQUEST.state }),
    ).toBeNull();
    expect(readDesktopRequest({ challenge: REQUEST.challenge })).toBeNull();
    expect(
      readDesktopRequest({ challenge: REQUEST.challenge, state: "<script>" }),
    ).toBeNull();
  });

  it("says so when the link did not come from the app", () => {
    render(<DesktopSignIn request={null} />);

    expect(
      screen.getByText(/did not come from the Jalada AI desktop app/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Allow" }),
    ).not.toBeInTheDocument();
  });

  it("asks before anything happens", () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<DesktopSignIn request={REQUEST} />);

    expect(screen.getByRole("button", { name: "Allow" })).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("sends the challenge, then opens the app with the code and the app's state", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ code: "one-time" }), { status: 201 }),
      );
    vi.stubGlobal("fetch", fetch);
    const location = { href: "" };
    vi.spyOn(window, "location", "get").mockReturnValue(location as Location);
    render(<DesktopSignIn request={REQUEST} />);

    fireEvent.click(screen.getByRole("button", { name: "Allow" }));

    await waitFor(() =>
      expect(location.href).toBe(
        `jalada://signed-in?code=one-time&state=${REQUEST.state}`,
      ),
    );
    expect(JSON.parse(fetch.mock.calls[0]![1].body)).toEqual({
      challenge: REQUEST.challenge,
    });
  });
});

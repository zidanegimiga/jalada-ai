import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConsentChoice } from "@/features/consent/components/ConsentChoice";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const NOTICE =
  "Google's Gemini API, in the United States. It does not train on your data.";
const ASKED = { required: true, given: false, notice: NOTICE };

function answers(given: boolean) {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ ...ASKED, given }), { status: 200 }),
    );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("ConsentChoice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("names the provider and what happens without it", () => {
    render(<ConsentChoice consent={ASKED} place="ask" />);

    expect(screen.getByText(NOTICE)).toBeInTheDocument();
    expect(screen.getByText(/outside Kenya/)).toBeInTheDocument();
    expect(screen.getByText(/Ask is off/)).toBeInTheDocument();
  });

  it("records the agreement and refreshes the page", async () => {
    const fetch = answers(true);
    render(<ConsentChoice consent={ASKED} place="ask" />);

    fireEvent.click(screen.getByRole("button", { name: "Allow" }));

    await vi.waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch).toHaveBeenCalledWith("/v1/account/model-consent", {
      method: "POST",
    });
  });

  it("lets the person take it back on the Account page", async () => {
    const fetch = answers(false);
    render(
      <ConsentChoice consent={{ ...ASKED, given: true }} place="account" />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Stop reading with AI" }),
    );

    expect(
      await screen.findByRole("button", { name: "Allow" }),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/v1/account/model-consent", {
      method: "DELETE",
    });
  });

  it("can be put off on Home without deciding", () => {
    const fetch = answers(true);
    render(<ConsentChoice consent={ASKED} place="home" />);

    fireEvent.click(screen.getByRole("button", { name: "Not now" }));

    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("shows nothing when no model is set up", () => {
    const { container } = render(
      <ConsentChoice
        consent={{ required: false, given: false, notice: "" }}
        place="home"
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe("ConsentChoice and the privacy notice", () => {
  it("points to the notice that lists every service", () => {
    render(
      <ConsentChoice
        consent={{ required: true, given: false, notice: "Google" }}
        place="ask"
      />,
    );

    expect(
      screen.getByRole("link", { name: "privacy notice" }),
    ).toHaveAttribute("href", "/privacy");
  });
});

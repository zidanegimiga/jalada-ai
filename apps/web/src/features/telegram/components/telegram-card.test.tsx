import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TelegramCard } from "./telegram-card";

describe("TelegramCard", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows nothing when the bot is not set up", () => {
    const { container } = render(
      <TelegramCard available={false} linked={false} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("says so once Telegram is linked", () => {
    render(<TelegramCard available linked />);

    expect(screen.getByText(/Telegram is linked/)).toBeInTheDocument();
  });

  it("gets a code and a link that opens the bot", async () => {
    const body = JSON.stringify({
      code: "ABCD2345",
      bot_link: "https://t.me/jalada_bot?start=ABCD2345",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(body, { status: 200 })),
    );
    render(<TelegramCard available linked={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Link Telegram" }));

    expect(await screen.findByText("ABCD2345")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Telegram" })).toHaveAttribute(
      "href",
      "https://t.me/jalada_bot?start=ABCD2345",
    );
  });
});

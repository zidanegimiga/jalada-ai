import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MessageDialog } from "@/features/evidence/components/MessageDialog";

const TEXT = "UKAB12CD34 Confirmed. Ksh150.00 sent to JANE WANJIKU 0712345678.";

describe("MessageDialog", () => {
  const writeText = vi.fn();

  beforeEach(() => {
    Object.assign(navigator, { clipboard: { writeText } });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    writeText.mockReset();
  });

  it("opens the message in place and copies its text", async () => {
    const fetchMock = vi.fn(async () => new Response(TEXT));
    vi.stubGlobal("fetch", fetchMock);
    render(<MessageDialog evidenceId="e1" received="Received 17 Nov 2026" />);

    fireEvent.click(screen.getByRole("button", { name: "Open message" }));

    expect(
      await screen.findByRole("dialog", { name: "Message" }),
    ).toBeInTheDocument();
    expect(await screen.findByText(TEXT)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/v1/evidence/e1/file");

    fireEvent.click(screen.getByRole("button", { name: "Copy text" }));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(TEXT));
    expect(
      await screen.findByRole("button", { name: "Copied" }),
    ).toBeInTheDocument();
  });

  it("says so when the message cannot be opened", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 404 })),
    );
    render(<MessageDialog evidenceId="e1" received="Received 17 Nov 2026" />);

    fireEvent.click(screen.getByRole("button", { name: "Open message" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Could not open the message.",
      ),
    );
    expect(screen.getByRole("button", { name: "Copy text" })).toBeDisabled();
  });
});

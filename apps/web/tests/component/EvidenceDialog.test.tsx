import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EvidenceDialog } from "@/features/evidence/components/EvidenceDialog";

const TEXT = "UKAB12CD34 Confirmed. Ksh150.00 sent to JANE WANJIKU 0712345678.";

describe("EvidenceDialog", () => {
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
    render(
      <EvidenceDialog
        evidenceId="e1"
        contentType="text/plain"
        description="Received 17 Nov 2026"
        trigger={<button type="button">Open message</button>}
      />,
    );

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
    render(
      <EvidenceDialog
        evidenceId="e1"
        contentType="text/plain"
        description="Received 17 Nov 2026"
        trigger={<button type="button">Open message</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open message" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Could not open the message.",
      ),
    );
    expect(screen.getByRole("button", { name: "Copy text" })).toBeDisabled();
  });

  it("shows a photo in place, with a link to open it full size", async () => {
    render(
      <EvidenceDialog
        evidenceId="e2"
        contentType="image/jpeg"
        trigger={<button type="button">See original</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "See original" }));

    expect(
      await screen.findByRole("img", { name: "The photo you sent" }),
    ).toHaveAttribute("src", "/v1/evidence/e2/file");
    expect(
      screen.getByRole("link", { name: "Open full size" }),
    ).toHaveAttribute("href", "/v1/evidence/e2/file");
  });
});

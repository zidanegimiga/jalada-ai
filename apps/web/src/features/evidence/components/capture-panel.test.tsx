import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CapturePanel } from "./capture-panel";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

function respond(status: number, body: unknown) {
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

const SAVED = { id: "1", content_type: "image/jpeg", duplicate: false };

describe("CapturePanel", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  it("uploads the chosen file and refreshes the list", async () => {
    const fetch = respond(201, SAVED);
    render(<CapturePanel />);
    const file = new File(["jpeg bytes"], "receipt.jpg", {
      type: "image/jpeg",
    });

    fireEvent.change(screen.getByLabelText("Photo or PDF"), {
      target: { files: [file] },
    });

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    const [path, init] = fetch.mock.calls[0];
    expect(path).toBe("/v1/evidence");
    expect((init.body as FormData).get("file")).toBe(file);
    expect(router.refresh).toHaveBeenCalled();
  });

  it("only offers photos and PDFs", () => {
    render(<CapturePanel />);

    expect(screen.getByLabelText("Photo or PDF")).toHaveAttribute(
      "accept",
      "image/jpeg,image/png,image/webp,application/pdf",
    );
  });

  it("pastes an M-Pesa message", async () => {
    const fetch = respond(201, { ...SAVED, content_type: "text/plain" });
    render(<CapturePanel />);

    fireEvent.click(
      screen.getByRole("button", { name: "Paste M-Pesa message" }),
    );
    fireEvent.change(screen.getByLabelText("M-Pesa message"), {
      target: { value: "UK4AB1CD25 Confirmed." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save message" }));

    await waitFor(() => expect(fetch).toHaveBeenCalled());
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      text: "UK4AB1CD25 Confirmed.",
    });
    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(screen.queryByLabelText("M-Pesa message")).not.toBeInTheDocument();
  });

  it("says when the same thing was already sent", async () => {
    respond(200, { ...SAVED, duplicate: true });
    render(<CapturePanel />);

    fireEvent.change(screen.getByLabelText("Photo or PDF"), {
      target: { files: [new File(["x"], "r.jpg")] },
    });

    expect(
      await screen.findByText("You already sent this one."),
    ).toBeInTheDocument();
  });

  it("shows the API's message when a file is refused", async () => {
    respond(415, {
      error: {
        code: "unsupported_file",
        message: "Send a photo (JPEG, PNG or WebP) or a PDF.",
      },
    });
    render(<CapturePanel />);

    fireEvent.change(screen.getByLabelText("Photo or PDF"), {
      target: { files: [new File(["x"], "notes.docx")] },
    });

    expect(await screen.findByText(/Send a photo/)).toBeInTheDocument();
    expect(router.refresh).not.toHaveBeenCalled();
  });
});

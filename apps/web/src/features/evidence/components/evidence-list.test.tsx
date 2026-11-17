import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { EvidenceItem } from "../api";
import { EvidenceList } from "./evidence-list";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

function item(overrides: Partial<EvidenceItem>): EvidenceItem {
  return {
    id: "e1",
    source: "web_upload",
    kind: "unknown",
    status: "received",
    content_type: "image/jpeg",
    size_bytes: 10,
    received_at: "2026-11-05T09:00:00Z",
    duplicate: false,
    ...overrides,
  };
}

describe("EvidenceList", () => {
  it("explains the first steps when empty", () => {
    render(<EvidenceList items={[]} />);

    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(screen.queryByText(/Telegram/)).not.toBeInTheDocument();
  });

  it("mentions Telegram when the bot is on", () => {
    const { rerender } = render(
      <EvidenceList items={[]} telegram="unlinked" />,
    );
    expect(screen.getByText(/once you link it above/)).toBeInTheDocument();

    rerender(<EvidenceList items={[]} telegram="linked" />);
    expect(screen.getByText(/bot on Telegram/)).toBeInTheDocument();
  });

  it("names each item by type and shows a plain-language status", () => {
    render(
      <EvidenceList
        items={[
          item({ id: "a" }),
          item({
            id: "b",
            content_type: "application/pdf",
            status: "needs_review",
          }),
          item({
            id: "c",
            content_type: "text/plain; charset=utf-8",
            status: "confirmed",
          }),
        ]}
      />,
    );

    expect(screen.getByText("Photo")).toBeInTheDocument();
    expect(screen.getByText("Waiting to be read")).toBeInTheDocument();
    expect(screen.getByText("PDF")).toBeInTheDocument();
    expect(screen.getByText("Needs a look")).toBeInTheDocument();
    expect(screen.getByText("Message")).toBeInTheDocument();
    expect(screen.getByText("Saved to ledger")).toBeInTheDocument();
  });

  it("says when a copy was linked to a payment already recorded", () => {
    render(
      <EvidenceList
        items={[
          item({ id: "a", status: "linked" }),
          item({ id: "b", status: "duplicate" }),
          item({ id: "c", status: "candidate" }),
        ]}
      />,
    );

    expect(screen.getByText("Linked to a payment")).toBeInTheDocument();
    expect(screen.getByText("Already recorded")).toBeInTheDocument();
    expect(screen.getByText("Waiting for its payment")).toBeInTheDocument();
  });

  it("offers to put back evidence marked not a transaction", () => {
    render(
      <EvidenceList
        items={[
          item({ id: "a", status: "not_a_transaction" }),
          item({ id: "b", status: "confirmed" }),
        ]}
      />,
    );

    expect(screen.getAllByRole("button", { name: "Put back" })).toHaveLength(1);
  });

  it("links to the original through the API", () => {
    render(<EvidenceList items={[item({ id: "abc" })]} />);

    expect(screen.getByRole("link", { name: "Open photo" })).toHaveAttribute(
      "href",
      "/v1/evidence/abc/file",
    );
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { EvidenceItem } from "../api";
import { EvidenceList } from "./evidence-list";

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
  it("invites the first upload when empty", () => {
    render(<EvidenceList items={[]} />);

    expect(screen.getByText(/Nothing yet/)).toBeInTheDocument();
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

  it("links to the original through the API", () => {
    render(<EvidenceList items={[item({ id: "abc" })]} />);

    expect(screen.getByRole("link", { name: "Open photo" })).toHaveAttribute(
      "href",
      "/v1/evidence/abc/file",
    );
  });
});

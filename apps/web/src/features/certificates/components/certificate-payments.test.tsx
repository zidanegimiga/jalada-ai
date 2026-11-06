import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { entry } from "@/features/review/components/test-data";

import type { Certificate } from "../types";
import { CertificatePayments } from "./certificate-payments";

const router = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const certificate = entry({
  id: "cert-1",
  kind: "withholding_certificate",
  direction: "in",
  amount_cents: 4_000_000,
  tax_withheld_cents: 200_000,
  counterparty: "EXAMPLE CLIENT LTD",
  occurred_on: "2026-03-03",
});
const payment = entry({
  id: "pay-1",
  direction: "in",
  amount_cents: 3_800_000,
  counterparty: "EXAMPLE CLIENT LTD",
  occurred_on: "2026-03-05",
});

function data(overrides: Partial<Certificate> = {}): Certificate {
  return {
    certificate,
    expected_payment_cents: 3_800_000,
    linked_cents: 0,
    payments: [],
    suggestions: [payment],
    ...overrides,
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("CertificatePayments", () => {
  it("says what the client would have paid and warns while nothing is linked", () => {
    render(<CertificatePayments data={data()} />);

    expect(
      screen.getByText(/so they would have paid you KSh 38,000.00/),
    ).toBeInTheDocument();
    expect(screen.getByText(/counts this income twice/)).toBeInTheDocument();
  });

  it("links a suggested payment and refreshes", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(data({ payments: [payment] }))),
      );
    vi.stubGlobal("fetch", fetch);
    render(<CertificatePayments data={data()} />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Link KSh 38,000.00 from EXAMPLE CLIENT LTD on 5 Mar 2026",
      }),
    );

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    expect(fetch).toHaveBeenCalledWith(
      "/v1/certificates/cert-1/payments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ payment_id: "pay-1" }),
      }),
    );
  });

  it("shows why a link was refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({
              error: { message: "Too much for this certificate." },
            }),
            { status: 422 },
          ),
        ),
    );
    render(<CertificatePayments data={data()} />);

    fireEvent.click(screen.getByRole("button", { name: /^Link / }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Too much for this certificate.",
    );
  });

  it("unlinks a linked payment", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(data())));
    vi.stubGlobal("fetch", fetch);
    render(
      <CertificatePayments
        data={data({ payments: [payment], suggestions: [] })}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Unlink / }));

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "/v1/certificates/cert-1/payments/pay-1",
        expect.objectContaining({ method: "DELETE" }),
      ),
    );
  });
});

import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Closing } from "@/features/landing/components/Closing";
import { Hero } from "@/features/landing/components/Hero";
import { Questions } from "@/features/landing/components/Questions";
import { Ribbon } from "@/features/landing/components/Ribbon";
import { QUESTIONS, RIBBON } from "@/features/landing/content";

describe("landing sections", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("opens with the promise and a way to start", () => {
    vi.stubGlobal("matchMedia", () => ({ matches: false }));
    render(<Hero />);

    expect(
      screen.getByRole("heading", { level: 1, name: /Every shilling/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Start your records" }),
    ).toHaveAttribute("href", "/signup");
    expect(
      screen.getByRole("link", { name: "See how it works" }),
    ).toHaveAttribute("href", "#how");
  });

  it("lists what can be sent once for screen readers, not the looping copies", () => {
    render(<Ribbon />);

    const list = screen.getByRole("list");
    expect(within(list).getAllByRole("listitem")).toHaveLength(RIBBON.length);
  });

  it("answers each question in place", () => {
    render(<Questions />);

    for (const { q } of QUESTIONS) {
      expect(screen.getByText(q).closest("details")).toBeInTheDocument();
    }
  });

  it("ends with sign-up, sign-in and the privacy notice", () => {
    vi.stubGlobal("matchMedia", () => ({ matches: false }));
    render(<Closing />);

    for (const link of screen.getAllByRole("link", {
      name: "Create an account",
    })) {
      expect(link).toHaveAttribute("href", "/signup");
    }
    expect(
      screen.getByRole("link", { name: "I already have one" }),
    ).toHaveAttribute("href", "/signin");
    expect(
      screen.getByRole("link", { name: "Privacy notice" }),
    ).toHaveAttribute("href", "/privacy");
  });
});

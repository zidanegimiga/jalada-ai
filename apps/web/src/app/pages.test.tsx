import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import PageError from "./error";
import Loading from "./loading";
import NotFound from "./not-found";

const captureException = vi.fn();
vi.mock("@sentry/nextjs", () => ({
  captureException: (error: unknown) => captureException(error),
}));

describe("route screens", () => {
  it("reports a page error, offers to try again and shows its reference", () => {
    const reset = vi.fn();
    const error = Object.assign(new Error("boom"), { digest: "3506530424" });
    render(<PageError error={error} reset={reset} />);

    expect(captureException).toHaveBeenCalledWith(error);
    expect(
      screen.getByRole("heading", { name: "Something went wrong" }),
    ).toBeInTheDocument();
    expect(screen.getByText("3506530424")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(reset).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("link", { name: "Go home" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("leaves out the reference when there is none", () => {
    render(<PageError error={new Error("boom")} reset={vi.fn()} />);

    expect(screen.queryByText(/Reference/)).not.toBeInTheDocument();
  });

  it("says when a page does not exist", () => {
    render(<NotFound />);

    expect(
      screen.getByRole("heading", { name: "Nothing here" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go home" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("announces that a page is loading", () => {
    render(<Loading />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading the page");
  });
});

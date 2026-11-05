import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GoogleButton } from "./google-button";

describe("GoogleButton", () => {
  it("starts sign-in through the API", () => {
    render(<GoogleButton />);

    expect(screen.getByRole("link", { name: "Continue with Google" })).toHaveAttribute(
      "href",
      "/v1/auth/google/start",
    );
  });
});

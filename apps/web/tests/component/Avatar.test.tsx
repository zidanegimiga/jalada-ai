import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Avatar, initials } from "@/shared/components/Avatar";

describe("initials", () => {
  it("takes the first and last names", () => {
    expect(initials("Wanjiru Njeri Kamau")).toBe("WK");
    expect(initials("achieng")).toBe("A");
    expect(initials("  ")).toBe("?");
  });
});

describe("Avatar", () => {
  it("shows initials until there is a photo", () => {
    const { rerender, container } = render(<Avatar name="Otieno Odhiambo" />);
    expect(screen.getByText("OO")).toBeInTheDocument();

    rerender(<Avatar name="Otieno Odhiambo" src="/photo.webp" />);
    expect(container.querySelector("img")).toHaveAttribute(
      "src",
      "/photo.webp",
    );
  });
});

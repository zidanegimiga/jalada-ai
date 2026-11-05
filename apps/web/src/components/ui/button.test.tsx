import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Button } from "./button";

describe("Button", () => {
  it("renders an accessible button with its label", () => {
    render(<Button>Add evidence</Button>);

    expect(screen.getByRole("button", { name: "Add evidence" })).toBeInTheDocument();
  });

  it("calls its click handler when pressed", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save</Button>);

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is 48px tall by default so it is easy to tap", () => {
    render(<Button>Save</Button>);

    expect(screen.getByRole("button")).toHaveClass("h-12");
  });

  it("does not respond when disabled", () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Save
      </Button>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onClick).not.toHaveBeenCalled();
  });
});

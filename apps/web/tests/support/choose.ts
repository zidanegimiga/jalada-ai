import { fireEvent, screen } from "@testing-library/react";

/** Presses an element the way a mouse does: Base UI menus act on the full sequence. */
export function press(element: Element) {
  fireEvent.pointerDown(element, { pointerType: "mouse" });
  fireEvent.mouseDown(element);
  fireEvent.pointerUp(element, { pointerType: "mouse" });
  fireEvent.mouseUp(element);
  fireEvent.click(element);
}

/** Opens the select named `label` and picks `option` from its list. */
export async function chooseOption(label: string | RegExp, option: string) {
  fireEvent.click(screen.getByRole("combobox", { name: label }));
  press(await screen.findByRole("option", { name: option }));
}

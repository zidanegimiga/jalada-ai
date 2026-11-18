import { createCn } from "cn/config";

/**
 * The token names from globals.css, by scale. cn needs them to know that text-lead is a
 * size and not a colour; without them it drops a colour class such as
 * text-primary-foreground when a size token comes after it.
 */
export const TOKENS = {
  text: [
    "tiny",
    "small",
    "body",
    "lead",
    "title",
    "amount",
    "total",
    "display",
    "hero",
  ],
  radius: ["card", "inset", "control"],
  spacing: ["gutter", "card", "section", "tap", "icon", "icon-lg"],
  container: ["page", "wide", "content"],
  shadow: ["raised", "overlay", "float"],
};

/** Joins class names, letting later classes win over earlier ones of the same kind. */
export const cn = createCn({ extend: { theme: TOKENS } });

import type { Motion } from "./motion-kit";
import {
  conversation,
  count,
  grow,
  lines,
  rise,
  split,
  words,
} from "./reveal-motions";
import { depth, gather } from "./opening-motions";
import { draw, parallax, ribbon, sideways, stack } from "./scroll-motions";

export { playOpening } from "./opening-motions";
export type { Motion, MotionContext } from "./motion-kit";

/** Every effect, by the name an element gives in data-motion. */
export const MOTIONS: Record<string, Motion> = {
  lines,
  words,
  rise,
  parallax,
  count,
  ribbon,
  sideways,
  stack,
  depth,
  gather,
  conversation,
  grow,
  split,
  draw,
};

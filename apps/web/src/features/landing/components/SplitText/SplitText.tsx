import type { ReactNode } from "react";

/** A heading's lines, each behind its own mask so it can slide up into view. */
export function Lines({
  lines,
  intro = false,
}: {
  lines: ReactNode[];
  intro?: boolean;
}) {
  return lines.map((line, index) => (
    <span
      key={index}
      className="block overflow-hidden pb-[0.08em]"
      {...(intro ? { "data-intro-line": "" } : { "data-line": "" })}
    >
      <span className="block">{line}</span>
    </span>
  ));
}

/** Text cut into words, for effects that light them up one at a time. */
export function Words({ text }: { text: string }) {
  return text.split(" ").map((word, index) => (
    <span key={index} data-word="">
      {word}{" "}
    </span>
  ));
}

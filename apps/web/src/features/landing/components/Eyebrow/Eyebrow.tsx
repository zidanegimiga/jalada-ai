import type { ReactNode } from "react";

/** The small numbered label over each section. */
export function Eyebrow({
  number,
  children,
}: {
  number: string;
  children: ReactNode;
}) {
  return (
    <p className="flex items-center gap-3 font-mono text-tiny tracking-[0.18em] uppercase">
      <span className="rounded-full border border-current px-2.5 py-1">
        {number}
      </span>
      {children}
    </p>
  );
}

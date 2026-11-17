import type { CSSProperties } from "react";

import { JOURNEY } from "../../journey";
import "./JourneyPanel.css";

/** Two digits: 1 becomes "01". */
function numbered(index: number): string {
  return String(index + 1).padStart(2, "0");
}

/**
 * Beside the form: how a message becomes a tax return, and a word on privacy. Black in both
 * themes, with faint columns behind.
 */
export function JourneyPanel({ heading }: { heading: string }) {
  return (
    <aside
      aria-label="How Jalada AI works"
      className="relative isolate flex flex-col gap-8 overflow-hidden rounded-card bg-(--black) ring-1 ring-white/10 p-card text-(--ivory) motion-safe:animate-in motion-safe:fill-mode-backwards motion-safe:fade-in motion-safe:slide-in-from-right-8 motion-safe:delay-150 motion-safe:duration-700 sm:p-10"
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 grid grid-cols-5"
      >
        {JOURNEY.map(({ name }, index) => (
          <span
            key={name}
            className={index % 2 ? "bg-white/[0.035]" : undefined}
          />
        ))}
      </div>
      <p className="flex items-center gap-2 font-mono text-tiny tracking-wide uppercase opacity-70">
        <span
          aria-hidden="true"
          className="size-1.5 rounded-full bg-(--pumpkin)"
        />
        One message · five steps · one record
      </p>
      <h2 className="text-display">{heading}</h2>
      <ol className="flex flex-col gap-4">
        {JOURNEY.map(({ name, detail }, index) => (
          <li
            key={name}
            className="journey-step flex items-center gap-4"
            style={{ "--step": index } as CSSProperties}
          >
            <span className="journey-number flex size-9 shrink-0 items-center justify-center rounded-full border border-white/30 font-mono text-tiny font-bold">
              {numbered(index)}
            </span>
            <span className="flex flex-col">
              <span className="text-lead font-medium">{name}</span>
              <span className="text-small opacity-75">{detail}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-auto flex flex-col gap-2 rounded-inset border border-white/10 bg-white/5 p-5">
        <p className="font-mono text-tiny tracking-wide uppercase opacity-70">
          Private by design
        </p>
        <p className="text-small opacity-85">
          Your receipts and messages are encrypted when stored, and only you can
          open them.
        </p>
      </div>
    </aside>
  );
}

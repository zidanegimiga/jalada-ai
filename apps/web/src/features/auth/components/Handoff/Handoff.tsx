"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
} from "react";

import "./Handoff.css";

/** How long each part takes. The page changes under the cover, between the two. */
export const HANDOFF_MS = { cover: 650, hold: 300, reveal: 750 } as const;

const COLUMNS = 5;

type Phase = "idle" | "covering" | "revealing";

const HandoffContext = createContext<(href: string, label: string) => void>(
  () => {},
);

/** Wraps sign-in and sign-up so a HandoffLink can cover the page while it changes. */
export function AuthHandoff({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("idle");
  const [label, setLabel] = useState("");
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const go = useCallback(
    (href: string, destination: string) => {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
        router.push(href);
        return;
      }
      timers.current.forEach(clearTimeout);
      setLabel(destination);
      setPhase("covering");
      const { cover, hold, reveal } = HANDOFF_MS;
      timers.current = [
        setTimeout(() => router.push(href), cover),
        setTimeout(() => setPhase("revealing"), cover + hold),
        setTimeout(() => setPhase("idle"), cover + hold + reveal),
      ];
    },
    [router],
  );

  return (
    <HandoffContext.Provider value={go}>
      {children}
      {phase !== "idle" && <Cover phase={phase} label={label} />}
    </HandoffContext.Provider>
  );
}

function Cover({ phase, label }: { phase: Phase; label: string }) {
  return (
    <div
      aria-hidden="true"
      data-phase={phase}
      className="fixed inset-0 z-[60] grid grid-cols-5 overflow-hidden"
    >
      {Array.from({ length: COLUMNS }, (_, column) => (
        <span
          key={column}
          className="handoff-column bg-(--black)"
          style={{ "--column": column } as CSSProperties}
        />
      ))}
      <div className="handoff-centre absolute inset-0 flex flex-col items-center justify-center gap-4 px-gutter text-(--ivory)">
        <p className="flex items-center gap-2 font-mono text-tiny tracking-wide uppercase opacity-70">
          <Image
            src="/mark.webp"
            alt=""
            width={18}
            height={18}
            unoptimized
            className="rounded-[0.3rem]"
          />
          Jalada AI
        </p>
        <p className="text-display">{label}</p>
        <div className="relative mt-2 h-px w-64 max-w-full border-t border-dashed border-white/40">
          <span className="handoff-dot absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-(--pumpkin) shadow-[0_0_0_6px_rgb(235_113_46_/_0.25)]" />
        </div>
      </div>
    </div>
  );
}

/** A link between sign-in and sign-up that plays the hand-off on the way. */
export function HandoffLink({
  href,
  destination,
  children,
  className,
}: {
  href: string;
  /** What the cover says while the page changes: "Create account". */
  destination: string;
  children: ReactNode;
  className?: string;
}) {
  const go = useContext(HandoffContext);
  function onClick(event: MouseEvent<HTMLAnchorElement>) {
    // Let new tabs and windows open as usual.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0)
      return;
    event.preventDefault();
    go(href, destination);
  }
  return (
    <Link href={href} onClick={onClick} className={className}>
      {children}
    </Link>
  );
}

"use client";

import { Dialog as Base } from "@base-ui/react/dialog";
import { X } from "lucide-react";
import type { ReactElement, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

type DrawerProps = {
  /** The control that opens it. */
  trigger: ReactElement;
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
  className?: string;
};

/**
 * A panel that slides in from the right edge, for lists that sit beside the page on a wide
 * screen. Escape, the close button or a tap outside closes it; so should picking from it.
 */
export function Drawer({
  trigger,
  title,
  open,
  onOpenChange,
  children,
  className,
}: DrawerProps) {
  return (
    <Base.Root open={open} onOpenChange={onOpenChange}>
      <Base.Trigger render={trigger} />
      <Base.Portal>
        <Base.Backdrop className="fixed inset-0 z-50 bg-black/40 transition-opacity duration-300 data-ending-style:opacity-0 data-starting-style:opacity-0" />
        <Base.Popup
          className={cn(
            "fixed inset-y-0 right-0 z-50 flex w-[min(22rem,88vw)] flex-col gap-4 bg-card px-4 pt-[calc(env(safe-area-inset-top)+1rem)] pb-[calc(env(safe-area-inset-bottom)+1rem)] text-card-foreground shadow-overlay outline-none transition-[translate] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] data-ending-style:translate-x-full data-starting-style:translate-x-full motion-reduce:transition-none",
            className,
          )}
        >
          <div className="flex items-center gap-3">
            <Base.Title className="flex-1 text-title">{title}</Base.Title>
            <Base.Close
              aria-label="Close"
              className="flex size-tap shrink-0 items-center justify-center rounded-full bg-muted transition-transform hover:rotate-90"
            >
              <X aria-hidden="true" className="size-icon" />
            </Base.Close>
          </div>
          <div className="-mx-4 flex-1 overflow-y-auto px-4">{children}</div>
        </Base.Popup>
      </Base.Portal>
    </Base.Root>
  );
}

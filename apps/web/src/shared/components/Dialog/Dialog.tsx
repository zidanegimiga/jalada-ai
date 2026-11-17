"use client";

import { Dialog as Base } from "@base-ui/react/dialog";
import { X } from "lucide-react";
import type { ReactElement, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

type DialogProps = {
  /** The control that opens it; it gets the dialog's open behaviour. */
  trigger: ReactElement;
  title: string;
  description?: string;
  children: ReactNode;
  onOpenChange?: (open: boolean) => void;
  className?: string;
};

/**
 * A sheet that slides up from the bottom on a phone and sits in the middle on a wide screen.
 * Escape, the close button or a tap outside closes it.
 */
export function Dialog({
  trigger,
  title,
  description,
  children,
  onOpenChange,
  className,
}: DialogProps) {
  return (
    <Base.Root onOpenChange={(open) => onOpenChange?.(open)}>
      <Base.Trigger render={trigger} />
      <Base.Portal>
        <Base.Backdrop className="fixed inset-0 z-50 bg-black/50 transition-opacity duration-300 data-ending-style:opacity-0 data-starting-style:opacity-0" />
        <Base.Popup
          className={cn(
            "fixed inset-x-0 bottom-0 z-50 mx-auto flex max-h-[85dvh] w-full max-w-page flex-col gap-4 rounded-t-card bg-card p-card pb-[calc(env(safe-area-inset-bottom)+1.25rem)] text-card-foreground shadow-overlay outline-none transition-[translate,opacity,scale] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] data-ending-style:translate-y-full data-starting-style:translate-y-full sm:top-1/2 sm:bottom-auto sm:-translate-y-1/2 sm:rounded-card sm:pb-card sm:data-ending-style:translate-y-[-45%] sm:data-ending-style:scale-95 sm:data-ending-style:opacity-0 sm:data-starting-style:translate-y-[-45%] sm:data-starting-style:scale-95 sm:data-starting-style:opacity-0",
            className,
          )}
        >
          <span
            aria-hidden="true"
            className="mx-auto -mt-2 h-1 w-10 rounded-full bg-border sm:hidden"
          />
          <div className="flex items-start gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <Base.Title className="text-title">{title}</Base.Title>
              {description && (
                <Base.Description className="text-small text-muted-foreground">
                  {description}
                </Base.Description>
              )}
            </div>
            <Base.Close
              aria-label="Close"
              className="flex size-tap shrink-0 items-center justify-center rounded-full bg-muted transition-transform hover:rotate-90"
            >
              <X aria-hidden="true" className="size-icon" />
            </Base.Close>
          </div>
          {children}
        </Base.Popup>
      </Base.Portal>
    </Base.Root>
  );
}

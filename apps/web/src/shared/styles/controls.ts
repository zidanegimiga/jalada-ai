/** The look every form control shares, so a select or a picker sits beside an input. */
export const CONTROL =
  "flex h-12 w-full min-w-0 items-center gap-2 rounded-control border border-input bg-card px-4 text-left text-body transition-colors hover:border-foreground/40 focus-visible:border-ring disabled:pointer-events-none disabled:opacity-50 data-popup-open:border-foreground dark:bg-input/30";

export const CONTROL_LABEL =
  "flex items-center gap-2 text-body leading-none font-medium";

/** A floating panel that grows out of the control that opened it. */
export const POPUP =
  "origin-(--transform-origin) rounded-inset border border-border bg-popover p-1 text-popover-foreground shadow-overlay outline-none transition-[scale,opacity] duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] data-ending-style:scale-95 data-ending-style:opacity-0 data-starting-style:scale-95 data-starting-style:opacity-0";

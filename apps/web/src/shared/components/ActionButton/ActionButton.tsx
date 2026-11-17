import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { ArrowRight, LoaderCircle, type LucideIcon } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

const EASE = "ease-[cubic-bezier(0.16,1,0.3,1)]";

/**
 * The look of a main action: a wide slab with the label on the left and a pumpkin tile on the
 * right. Under the pointer the slab warms and the tile's icon slides; pressing gives a little.
 */
const ACTION = cn(
  "group/action flex min-h-15 w-full items-center justify-between gap-3 rounded-inset bg-foreground py-2 pr-2 pl-6 text-left text-lead font-medium tracking-tight text-background transition-[background-color,scale] duration-300 select-none hover:bg-(--action-hover) active:scale-[0.985] disabled:pointer-events-none disabled:opacity-60 aria-disabled:pointer-events-none aria-disabled:opacity-60",
  EASE,
);

function Tile({ icon, busy }: { icon: LucideIcon; busy?: boolean }) {
  const Icon = busy ? LoaderCircle : icon;
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-11 shrink-0 items-center justify-center rounded-control bg-primary text-primary-foreground transition-[background-color,scale] duration-500 group-hover/action:bg-(--action-tile-hover) group-active/action:scale-90",
        EASE,
      )}
    >
      <Icon
        className={cn(
          "size-icon transition-transform duration-500 group-hover/action:translate-x-1",
          EASE,
          busy && "motion-safe:animate-spin",
        )}
      />
    </span>
  );
}

type ActionProps = {
  children: ReactNode;
  /** The tile's icon: an arrow unless the action is better shown, such as a download. */
  icon?: LucideIcon;
  /** Working on it: the tile spins and the button cannot be pressed again. */
  busy?: boolean;
  className?: string;
};

export function ActionButton({
  children,
  icon = ArrowRight,
  busy = false,
  className,
  disabled,
  ...props
}: ActionProps & Omit<ButtonPrimitive.Props, "children" | "className">) {
  return (
    <ButtonPrimitive
      className={cn(ACTION, className)}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      {...props}
    >
      <span>{children}</span>
      <Tile icon={icon} busy={busy} />
    </ButtonPrimitive>
  );
}

/** The same look for a link, such as a download. */
export function ActionLink({
  children,
  icon = ArrowRight,
  className,
  ...props
}: Omit<ActionProps, "busy"> &
  Omit<ComponentProps<"a">, "children" | "className">) {
  return (
    <a className={cn(ACTION, className)} {...props}>
      <span>{children}</span>
      <Tile icon={icon} />
    </a>
  );
}

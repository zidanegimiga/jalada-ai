import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type EmptyStateProps = {
  Icon: LucideIcon;
  title: string;
  /** What happens here, and the next step. */
  children: ReactNode;
  /** A link or button to that next step. */
  action?: ReactNode;
};

/** Shown in place of an empty list, so a new user knows what to do next. */
export function EmptyState({ Icon, title, children, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card bg-muted px-card py-8 text-center motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:duration-500">
      <span className="flex size-14 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
        <Icon aria-hidden="true" className="size-icon-lg" />
      </span>
      <p className="text-title">{title}</p>
      <div className="flex flex-col gap-2 text-muted-foreground">
        {children}
      </div>
      {action}
    </div>
  );
}

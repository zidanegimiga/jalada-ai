import type { CSSProperties, ReactNode } from "react";

import { cn } from "@/shared/styles/cn";

/** The folder colours: ink like the month card, or flax like a document folder. */
const TONES = {
  ink: {
    fill: "light-dark(var(--black), #1f1e1a)",
    text: "text-(--ivory)",
    tab: "text-(--ivory)/70",
  },
  flax: {
    fill: "light-dark(var(--flax), #2e2a14)",
    text: "text-(--black) dark:text-(--flax)",
    tab: "text-(--black)/70 dark:text-(--flax)/80",
  },
} as const;

type FolderCardProps = {
  /** The words on the tab, such as "This month". */
  tab: string;
  tone?: keyof typeof TONES;
  children: ReactNode;
  className?: string;
} & Pick<
  React.ComponentProps<"section">,
  "aria-label" | "aria-labelledby" | "aria-busy"
>;

/**
 * A card shaped like a folder, with a tab on its top edge, echoing the logo. The tab joins
 * the card with a curve cut from a radial gradient.
 */
export function FolderCard({
  tab,
  tone = "ink",
  children,
  className,
  ...aria
}: FolderCardProps) {
  const style = TONES[tone];
  return (
    <section
      {...aria}
      className={cn("flex flex-col", style.text)}
      style={{ "--folder": style.fill } as CSSProperties}
    >
      <div className="flex items-end">
        <p
          className={cn(
            "rounded-t-inset bg-(--folder) pt-2 pr-4 pb-1 pl-card font-mono text-tiny tracking-widest uppercase",
            style.tab,
          )}
        >
          {tab}
        </p>
        <span
          aria-hidden="true"
          className="size-4 bg-[radial-gradient(circle_at_100%_0,transparent_1rem,var(--folder)_calc(1rem+0.5px))]"
        />
      </div>
      <div
        className={cn(
          "flex flex-col gap-5 rounded-card rounded-tl-none bg-(--folder) p-card",
          className,
        )}
      >
        {children}
      </div>
    </section>
  );
}

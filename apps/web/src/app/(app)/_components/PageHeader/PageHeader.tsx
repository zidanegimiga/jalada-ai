import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  /** The page's name, read as its main heading. Leave out when the page has its own. */
  title?: ReactNode;
  /** A small line over the title, or in its place when the page has its own heading. */
  eyebrow?: string;
  /** Where the back button goes, and the name of that place. */
  back?: { href: string; label: string };
  /** Buttons on the right of the title. */
  actions?: ReactNode;
  /** Links to the page's own sections, shown under the title on wide screens. */
  jumps?: { href: string; label: string }[];
};

/**
 * The top of each signed-in page: back, the title and the page's own buttons. On wide
 * screens it stays at the top while the page scrolls under it, so every section of the page
 * is one click away.
 */
export function PageHeader({ title, eyebrow, back, actions, jumps }: Props) {
  return (
    <header className="z-30 -mx-gutter flex flex-col gap-3 bg-background px-gutter pb-1 lg:sticky lg:top-0 lg:border-b lg:border-border lg:pt-8 lg:pb-4">
      <div className="flex items-center gap-3">
        {back && (
          <Link
            href={back.href}
            aria-label={`Back to ${back.label}`}
            className="grid size-tap shrink-0 place-items-center rounded-full bg-muted text-foreground transition-[background-color,translate] hover:-translate-x-0.5 hover:bg-secondary"
          >
            <ArrowLeft aria-hidden="true" className="size-icon" />
          </Link>
        )}
        <div className="min-w-0 flex-1">
          {eyebrow && (
            <p className="font-mono text-tiny tracking-wider text-muted-foreground uppercase">
              {eyebrow}
            </p>
          )}
          {title && <h1 className="truncate text-display">{title}</h1>}
        </div>
        {actions}
      </div>
      {jumps && jumps.length > 0 && (
        <nav aria-label="On this page" className="hidden lg:block">
          <ul className="flex flex-wrap gap-1.5">
            {jumps.map((jump) => (
              <li key={jump.href}>
                <a
                  href={jump.href}
                  className="inline-flex min-h-tap items-center rounded-full bg-muted px-4 text-small font-medium transition-colors hover:bg-secondary hover:text-secondary-foreground"
                >
                  {jump.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}

import { describeEvent } from "../../history";
import type { HistoryItem } from "../../types";

const WHEN = new Intl.DateTimeFormat("en-KE", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** What happened to the payment, oldest first, along a line with a dot for each event. */
export function EntryHistory({ history }: { history: HistoryItem[] }) {
  if (history.length === 0) return null;
  return (
    <section aria-labelledby="history-heading" className="flex flex-col gap-3">
      <h2 id="history-heading" className="text-title">
        History
      </h2>
      <ol className="relative flex flex-col gap-5 rounded-card border border-border bg-card p-card">
        <span
          aria-hidden="true"
          className="absolute top-8 bottom-8 left-[calc(var(--spacing-card)+0.4rem)] w-px bg-border"
        />
        {history.map((item, index) => {
          const { title, detail } = describeEvent(item);
          const last = index === history.length - 1;
          return (
            <li key={`${item.at}-${index}`} className="relative flex gap-4">
              <span
                aria-hidden="true"
                className={
                  last
                    ? "relative mt-1.5 size-3.5 shrink-0 rounded-full bg-primary ring-4 ring-primary/20"
                    : "relative mt-1.5 size-3.5 shrink-0 rounded-full border-2 border-foreground/40 bg-card"
                }
              />
              <div className="flex flex-col">
                <p className="font-medium">{title}</p>
                {detail && <p className="text-muted-foreground">{detail}</p>}
                <p className="font-mono text-tiny text-muted-foreground">
                  <time dateTime={item.at}>
                    {WHEN.format(new Date(item.at))}
                  </time>
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

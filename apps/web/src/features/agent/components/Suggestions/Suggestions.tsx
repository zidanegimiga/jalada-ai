export const SUGGESTIONS = [
  "How much did I spend this month?",
  "Is anything waiting for me to check?",
  "Where did my money go this year?",
  "Can I get last year's workbook?",
] as const;

/** Questions to start with, for someone who has not asked anything yet. */
export function Suggestions({
  onPick,
  disabled,
}: {
  onPick: (question: string) => void;
  disabled: boolean;
}) {
  return (
    <section
      aria-labelledby="suggestions-heading"
      className="flex flex-col gap-3"
    >
      <h2 id="suggestions-heading" className="text-muted-foreground">
        Ask about your own payments, receipts and messages. Answers come from
        your records only.
      </h2>
      <ul className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((question) => (
          <li key={question}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(question)}
              className="min-h-tap rounded-full border border-border bg-card px-4 py-2 text-left text-small transition-colors hover:bg-muted disabled:opacity-50"
            >
              {question}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

import { formatKsh } from "@/shared/format/format";
import { cn } from "@/shared/styles/cn";

/**
 * A shilling amount. The figures are tabular, so amounts in a list line up digit by digit,
 * and an amount never breaks across two lines. With `fadeCents`, as on a balance, "KSh" is
 * small and the cents fade back so the shillings carry the eye. Screen readers hear the
 * plain amount either way.
 */
export function Amount({
  cents,
  fadeCents = false,
  className,
}: {
  cents: number;
  fadeCents?: boolean;
  className?: string;
}) {
  const text = formatKsh(cents);
  if (!fadeCents) {
    return (
      <span className={cn("whitespace-nowrap tabular-nums", className)}>
        {text}
      </span>
    );
  }
  const [currency, figure] = text.split(" ");
  const [shillings, fraction] = figure.split(".");
  return (
    <span className={cn("whitespace-nowrap tabular-nums", className)}>
      <span className="sr-only">{text}</span>
      <span aria-hidden="true">
        <span className="mr-1 align-[0.3em] text-[0.55em] font-medium opacity-70">
          {currency}
        </span>
        {shillings}
        <span className="opacity-45">.{fraction}</span>
      </span>
    </span>
  );
}

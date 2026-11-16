import { formatKsh } from "@/lib/format";

/** A shilling amount. The figures are tabular, so amounts in a list line up digit by
 * digit, and an amount never breaks across two lines. */
export function Amount({ cents }: { cents: number }) {
  return (
    <span className="whitespace-nowrap tabular-nums">{formatKsh(cents)}</span>
  );
}

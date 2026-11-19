import { LEDGER } from "../../content";

/** The ledger the opening's evidence turns into. */
export function HeroLedger() {
  return (
    <div
      data-ledger=""
      className="w-full max-w-[34rem] rounded-[2rem] bg-(--l-ink) p-5 text-(--l-paper) shadow-[0_40px_80px_-30px_rgb(0_0_0/0.55)] md:p-7"
    >
      <div className="flex items-baseline justify-between">
        <p className="font-mono text-tiny tracking-[0.16em] text-(--l-quiet-on-ink) uppercase">
          Ledger, November
        </p>
        <p className="font-mono text-tiny text-(--l-quiet-on-ink)">5 entries</p>
      </div>
      <p className="mt-3 text-[clamp(2rem,4vw,2.75rem)] leading-none font-bold tracking-tight tabular-nums">
        KES 119,300.00
      </p>
      <p className="mt-1 text-small text-(--l-quiet-on-ink)">
        money in this month, so far
      </p>
      <ul className="mt-6 divide-y divide-white/10">
        {LEDGER.map((row) => (
          <li
            key={row.name}
            data-row=""
            className="flex items-center gap-3 py-3"
          >
            <span
              aria-hidden="true"
              className="grid size-9 shrink-0 place-items-center rounded-full bg-white/8 text-small font-bold"
            >
              {row.name[0]}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-body font-medium">
                {row.name}
              </span>
              <span className="block text-tiny text-(--l-quiet-on-ink)">
                {row.category}
              </span>
            </span>
            <span className="text-right">
              <span
                className={`block text-body font-bold tabular-nums ${row.amount.startsWith("+") ? "text-(--l-in)" : ""}`}
              >
                {row.amount}
              </span>
              <span
                className={`block font-mono text-[0.625rem] tracking-wider uppercase ${row.state === "To check" ? "text-(--l-pumpkin)" : "text-(--l-quiet-on-ink)"}`}
              >
                {row.state}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

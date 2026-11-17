"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { buttonVariants } from "@/shared/components/Button";
import { MonthPicker } from "@/shared/components/MonthPicker";

const CHOICES = {
  direction: [
    ["", "All"],
    ["in", "Money in"],
    ["out", "Money out"],
  ],
  purpose: [
    ["", "All"],
    ["business", "Business"],
    ["personal", "Personal"],
  ],
} as const;

/** Filters live in the address, so a filtered ledger can be bookmarked or shared. */
export function LedgerFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  function set(name: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    next.delete("cursor");
    router.replace(`${pathname}?${next}`);
  }

  return <FilterControls params={params} onChange={set} />;
}

/** The same controls, held still while the address is read, so the page does not move. */
export function LedgerFiltersSkeleton() {
  return (
    <FilterControls
      params={new URLSearchParams()}
      onChange={() => {}}
      disabled
    />
  );
}

function FilterControls({
  params,
  onChange: set,
  disabled = false,
}: {
  params: URLSearchParams;
  onChange: (name: string, value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      <MonthPicker
        label="Month"
        value={params.get("month") ?? ""}
        onChange={(month) => set("month", month)}
        disabled={disabled}
      />
      {(Object.keys(CHOICES) as (keyof typeof CHOICES)[]).map((name) => (
        <div
          key={name}
          role="group"
          aria-label={name === "direction" ? "Direction" : "Purpose"}
          className="flex flex-wrap gap-2"
        >
          {CHOICES[name].map(([value, label]) => {
            const active = (params.get(name) ?? "") === value;
            return (
              <button
                key={label}
                type="button"
                aria-pressed={active}
                disabled={disabled}
                onClick={() => set(name, value)}
                className={buttonVariants({
                  variant: active ? "default" : "outline",
                  size: "sm",
                })}
              >
                {label}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

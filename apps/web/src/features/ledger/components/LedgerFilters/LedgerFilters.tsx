"use client";

import {
  ArrowDownLeft,
  ArrowUpRight,
  BriefcaseBusiness,
  UserRound,
  X,
} from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { ChipTabs } from "@/shared/components/ChipTabs";
import { MonthPicker } from "@/shared/components/MonthPicker";

/** Each filter's chips; the empty value means no filter. */
const CHOICES = {
  direction: {
    label: "Direction",
    chips: [
      { value: "", label: "All" },
      { value: "in", label: "Money in", Icon: ArrowDownLeft },
      { value: "out", label: "Money out", Icon: ArrowUpRight },
    ],
  },
  purpose: {
    label: "Purpose",
    chips: [
      { value: "", label: "All" },
      { value: "business", label: "Business", Icon: BriefcaseBusiness },
      { value: "personal", label: "Personal", Icon: UserRound },
    ],
  },
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

  return (
    <FilterControls
      params={params}
      onChange={set}
      onClear={() => router.replace(pathname)}
    />
  );
}

/** The same controls, held still while the address is read, so the page does not move. */
export function LedgerFiltersSkeleton() {
  return (
    <FilterControls
      params={new URLSearchParams()}
      onChange={() => {}}
      onClear={() => {}}
      disabled
    />
  );
}

function FilterControls({
  params,
  onChange: set,
  onClear,
  disabled = false,
}: {
  params: URLSearchParams;
  onChange: (name: string, value: string) => void;
  onClear: () => void;
  disabled?: boolean;
}) {
  const filtered = ["month", ...Object.keys(CHOICES)].some((name) =>
    params.get(name),
  );
  return (
    <section
      aria-label="Filters"
      className="flex flex-col gap-3 rounded-card border border-border bg-card p-3"
    >
      <div className="flex items-center gap-2">
        <MonthPicker
          label="Month"
          compact
          value={params.get("month") ?? ""}
          onChange={(month) => set("month", month)}
          disabled={disabled}
        />
        {filtered && (
          <button
            type="button"
            onClick={onClear}
            className="ml-auto inline-flex min-h-tap items-center gap-1.5 rounded-full px-3 text-small font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <X aria-hidden="true" className="size-4" />
            Clear filters
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {(Object.keys(CHOICES) as (keyof typeof CHOICES)[]).map((name) => (
          <ChipTabs
            key={name}
            label={CHOICES[name].label}
            chips={CHOICES[name].chips}
            value={params.get(name) ?? ""}
            onChange={(value) => set(name, value)}
            disabled={disabled}
          />
        ))}
      </div>
    </section>
  );
}

"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { ChipTabs } from "@/shared/components/ChipTabs";
import { MonthPicker } from "@/shared/components/MonthPicker";

/** Each filter's chips; the empty value means no filter. */
const CHOICES = {
  direction: {
    label: "Direction",
    chips: [
      { value: "", label: "All" },
      { value: "in", label: "Money in" },
      { value: "out", label: "Money out" },
    ],
  },
  purpose: {
    label: "Purpose",
    chips: [
      { value: "", label: "All" },
      { value: "business", label: "Business" },
      { value: "personal", label: "Personal" },
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
    </div>
  );
}

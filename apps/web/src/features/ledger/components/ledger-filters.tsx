"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

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

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="month">Month</Label>
        <input
          id="month"
          type="month"
          value={params.get("month") ?? ""}
          onChange={(e) => set("month", e.target.value)}
          className="h-12 rounded-xl border border-input bg-card px-4 text-base"
        />
      </div>
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

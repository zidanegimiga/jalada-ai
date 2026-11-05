"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { buttonVariants } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

/** Download one tax year (1 January to 31 December) as an Excel workbook for filing. */
export function ExportCard({ currentYear }: { currentYear: number }) {
  const years = [currentYear, currentYear - 1, currentYear - 2];
  // Returns are filed for last year, so that is the usual choice.
  const [year, setYear] = useState(currentYear - 1);

  return (
    <section
      aria-labelledby="export-heading"
      className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-5"
    >
      <h2 id="export-heading" className="text-xl font-bold">
        For your tax return
      </h2>
      <p className="text-muted-foreground">
        Confirmed entries for one year, grouped the way iTax asks for them.
      </p>
      <Label htmlFor="export-year">Year</Label>
      <select
        id="export-year"
        value={year}
        onChange={(event) => setYear(Number(event.target.value))}
        className="h-12 rounded-xl border border-input bg-card px-4 text-base"
      >
        {years.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <a
        href={`/v1/exports/${year}.xlsx`}
        download
        className={buttonVariants({ size: "lg" })}
      >
        <Download aria-hidden="true" />
        Download {year} (Excel)
      </a>
    </section>
  );
}

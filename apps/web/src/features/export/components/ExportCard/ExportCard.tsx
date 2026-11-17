"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { buttonVariants } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";

/** Download one tax year (1 January to 31 December) as an Excel workbook for filing. */
export function ExportCard({
  currentYear,
  defaultYear,
}: {
  currentYear: number;
  defaultYear: number;
}) {
  const years = [currentYear, currentYear - 1, currentYear - 2];
  const [year, setYear] = useState(defaultYear);

  return (
    <section
      aria-labelledby="export-heading"
      className="flex flex-col gap-3 rounded-card border border-border bg-card p-card"
    >
      <h2 id="export-heading" className="text-title">
        For your tax return
      </h2>
      <p className="text-muted-foreground">
        Confirmed entries for one year, grouped the way iTax asks for them.
      </p>
      <Select
        label="Year"
        options={years.map((option) => ({
          value: String(option),
          label: String(option),
        }))}
        value={String(year)}
        onValueChange={(next) => setYear(Number(next))}
      />
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

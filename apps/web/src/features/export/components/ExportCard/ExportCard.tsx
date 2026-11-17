"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { ActionLink } from "@/shared/components/ActionButton";
import { FolderCard } from "@/shared/components/FolderCard";
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
    <FolderCard
      tab="Tax return"
      tone="flax"
      aria-labelledby="export-heading"
      className="gap-3"
    >
      <h2 id="export-heading" className="text-title">
        For your tax return
      </h2>
      <p className="opacity-75">
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
      <ActionLink href={`/v1/exports/${year}.xlsx`} download icon={Download}>
        Download {year} (Excel)
      </ActionLink>
    </FolderCard>
  );
}

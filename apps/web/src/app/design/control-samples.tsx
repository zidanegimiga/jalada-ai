"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { ActionButton, ActionLink } from "@/shared/components/ActionButton";
import { DatePicker } from "@/shared/components/DatePicker";
import { MonthPicker } from "@/shared/components/MonthPicker";
import { Select } from "@/shared/components/Select";

/** The interactive controls, live, so their motion can be tried on this page. */
export function ControlSamples() {
  const [month, setMonth] = useState("");
  return (
    <>
      <ActionButton>Sign in</ActionButton>
      <ActionLink href="#components" icon={Download}>
        Download 2025 (Excel)
      </ActionLink>
      <Select
        label="What it was for"
        options={[
          { value: "food", label: "Food" },
          { value: "stock", label: "Stock and supplies" },
        ]}
      />
      <MonthPicker label="Month" value={month} onChange={setMonth} />
      <DatePicker label="Date" name="sample_date" />
    </>
  );
}

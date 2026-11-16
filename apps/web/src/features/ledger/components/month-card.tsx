import { formatKsh } from "@/lib/format";

import type { Month } from "../types";

const monthName = new Intl.DateTimeFormat("en-KE", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

function Row({
  label,
  business,
  personal,
}: {
  label: string;
  business: number;
  personal: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-small opacity-80">{label}</p>
      <p className="text-total">{formatKsh(business + personal)}</p>
      <p className="text-small opacity-80">
        Business {formatKsh(business)} · Personal {formatKsh(personal)}
      </p>
    </div>
  );
}

/** The month at a glance, in the style of a balance card. Only confirmed entries count. */
export function MonthCard({ year, month }: { year: number; month: Month }) {
  return (
    <section
      aria-label="This month"
      className="flex flex-col gap-5 rounded-card bg-foreground p-card text-background dark:border dark:border-border dark:bg-card dark:text-card-foreground"
    >
      <h2 className="text-lead font-medium">
        {monthName.format(new Date(Date.UTC(year, month.month - 1, 1)))}
      </h2>
      <Row
        label="Money in"
        business={month.in_business_cents}
        personal={month.in_personal_cents}
      />
      <Row
        label="Money out"
        business={month.out_business_cents}
        personal={month.out_personal_cents}
      />
    </section>
  );
}

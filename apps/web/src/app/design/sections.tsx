import type { ReactNode } from "react";
import { Receipt } from "lucide-react";

import { Amount } from "@/shared/components/Amount";
import { Button } from "@/shared/components/Button";
import { Input } from "@/shared/components/Input";
import { Label } from "@/shared/components/Label";

import { ControlSamples } from "./control-samples";
import { COLOURS, ICONS, RADII, SHADOWS, SPACING, TYPE } from "./tokens";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-title">{title}</h2>
      {children}
    </section>
  );
}

function Row({
  name,
  use,
  children,
}: {
  name: string;
  use: string;
  children: ReactNode;
}) {
  return (
    <li className="flex items-center justify-between gap-4 py-3">
      <span className="flex flex-col">
        <code className="text-small">{name}</code>
        <span className="text-small text-muted-foreground">{use}</span>
      </span>
      {children}
    </li>
  );
}

const LIST = "flex flex-col divide-y divide-border";

export function Colours() {
  return (
    <Section title="Colours">
      <ul className="grid grid-cols-2 gap-3">
        {COLOURS.map((name) => (
          <li key={name} className="flex items-center gap-3">
            <span
              className="size-10 shrink-0 rounded-control border border-border"
              style={{ background: `var(--${name})` }}
            />
            <code className="text-small">{name}</code>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export function Type() {
  return (
    <Section title="Type">
      <ul className={LIST}>
        {TYPE.map(({ name, className, use, sample }) => (
          <li key={name} className="flex flex-col gap-1 py-3">
            <span className={className}>{sample}</span>
            <span className="text-small text-muted-foreground">
              <code>text-{name}</code> · {use}
            </span>
          </li>
        ))}
      </ul>
      <p className="text-muted-foreground">
        Amounts use tabular figures, so they line up: <Amount cents={11100} />{" "}
        and <Amount cents={88800} />.
      </p>
    </Section>
  );
}

export function Shapes() {
  return (
    <Section title="Radii, spacing and elevation">
      <ul className={LIST}>
        {RADII.map(({ name, use }) => (
          <Row key={name} name={`rounded-${name}`} use={use}>
            <span
              className="h-12 w-20 border border-border bg-secondary"
              style={{ borderRadius: `var(--radius-${name})` }}
            />
          </Row>
        ))}
        {SPACING.map(({ name, use }) => (
          <Row key={name} name={`p-${name}`} use={use}>
            <span
              className="h-3 bg-primary"
              style={{ width: `var(--spacing-${name})` }}
            />
          </Row>
        ))}
        {SHADOWS.map(({ name, use }) => (
          <Row key={name} name={`shadow-${name}`} use={use}>
            <span
              className="size-12 rounded-control bg-card"
              style={{ boxShadow: `var(--shadow-${name})` }}
            />
          </Row>
        ))}
        {ICONS.map(({ name, use }) => (
          <Row key={name} name={`size-${name}`} use={use}>
            <Receipt
              aria-hidden="true"
              style={{
                width: `var(--spacing-${name})`,
                height: `var(--spacing-${name})`,
              }}
            />
          </Row>
        ))}
      </ul>
    </Section>
  );
}

export function Components() {
  return (
    <Section title="Components">
      <div className="flex flex-wrap gap-3">
        <Button>Confirm</Button>
        <Button variant="outline">Change</Button>
        <Button variant="ghost">Undo</Button>
        <Button size="sm" variant="outline">
          Sign out
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="design-sample">Amount</Label>
        <Input id="design-sample" inputMode="decimal" placeholder="1,250.00" />
      </div>
      <p className="rounded-inset bg-secondary px-4 py-3 text-secondary-foreground">
        A note inside a card, such as a question about a payment.
      </p>
      <ControlSamples />
    </Section>
  );
}

import type { ComponentProps } from "react";

type AuthFieldProps = ComponentProps<"input"> & {
  /** Its place in the form, shown before the label: "01". */
  number: string;
  label: string;
  name: string;
  /** A line under the field, read out with it. */
  hint?: string;
};

/**
 * A numbered field drawn as a single line. Focus draws a deep pumpkin underline across from
 * the left instead of a box.
 */
export function AuthField({
  number,
  label,
  name,
  id = name,
  hint,
  ...inputProps
}: AuthFieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline gap-3 font-mono text-tiny tracking-widest text-muted-foreground uppercase">
        <span aria-hidden="true" className="font-bold text-(--emphasis)">
          {number}
        </span>
        <label htmlFor={id}>{label}</label>
      </div>
      <div className="relative">
        <input
          id={id}
          name={name}
          required
          aria-describedby={hintId}
          className="peer h-12 w-full border-0 border-b border-border bg-transparent px-0 text-lead outline-none placeholder:text-muted-foreground/70 focus-visible:outline-none"
          {...inputProps}
        />
        <span
          aria-hidden="true"
          className="absolute inset-x-0 bottom-0 h-0.5 origin-left scale-x-0 bg-(--focus) transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] peer-focus:scale-x-100"
        />
      </div>
      {hint && (
        <p id={hintId} className="text-small text-muted-foreground">
          {hint}
        </p>
      )}
    </div>
  );
}

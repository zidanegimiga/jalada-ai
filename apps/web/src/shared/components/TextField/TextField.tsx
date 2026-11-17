import { Input } from "@/shared/components/Input";
import { Label } from "@/shared/components/Label";

type TextFieldProps = React.ComponentProps<"input"> & {
  label: string;
  name: string;
};

/** A labelled input. Pass `id` when the same form can appear more than once on a page. */
export function TextField({
  label,
  name,
  id = name,
  ...inputProps
}: TextFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} name={name} required {...inputProps} />
    </div>
  );
}

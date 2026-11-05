import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type FormFieldProps = React.ComponentProps<"input"> & {
  label: string;
  name: string;
};

/** A labelled input. Pass `id` when the same form can appear more than once on a page. */
export function FormField({
  label,
  name,
  id = name,
  ...inputProps
}: FormFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} name={name} required {...inputProps} />
    </div>
  );
}

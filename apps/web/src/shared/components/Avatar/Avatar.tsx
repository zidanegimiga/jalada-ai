import { cn } from "@/shared/styles/cn";

/** Up to two capital letters from a name: "Wanjiru Kamau" becomes "WK". */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? [words[0], words.at(-1)!] : words;
  return letters.map((word) => word[0]!.toUpperCase()).join("") || "?";
}

/**
 * A person's photo, or their initials on pumpkin until they add one. The name is read out,
 * so the picture itself is decoration.
 */
export function Avatar({
  name,
  src,
  className,
}: {
  name: string;
  src?: string | null;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "flex size-tap shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary text-small font-bold text-primary-foreground select-none",
        className,
      )}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element -- a user's photo from the API
        <img src={src} alt="" className="size-full object-cover" />
      ) : (
        <span aria-hidden="true">{initials(name)}</span>
      )}
    </span>
  );
}

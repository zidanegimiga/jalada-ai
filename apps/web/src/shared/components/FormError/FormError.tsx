/**
 * Where an action's error appears. The alert stays on the page with no text until there
 * is an error, so screen readers that only watch existing alerts still read it out.
 */
export function FormError({ message }: { message: string | null | undefined }) {
  return (
    <p role="alert" className={message ? "text-destructive" : "sr-only"}>
      {message}
    </p>
  );
}

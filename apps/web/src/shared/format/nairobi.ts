/** Today's year and month in Kenya, whatever time zone the server runs in. Call it after
 * `connection()` in a server component, so it is read per request. */
export function nairobiMonth(): { year: number; month: number } {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "2-digit",
  }).formatToParts(new Date());
  const value = (type: string) =>
    Number(parts.find((part) => part.type === type)?.value);
  return { year: value("year"), month: value("month") };
}

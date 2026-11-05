import { connection } from "next/server";

import { publicApiGet } from "@/lib/public-api";

import { GoogleButton } from "./google-button";

/** The Google button and divider, shown only when the API has Google sign-in switched on.
 * Checked on each request, so turning Google on needs no rebuild of the web app. */
export async function GoogleOption() {
  await connection();
  const options = await publicApiGet<{ google: boolean }>("/v1/auth/providers");
  if (!options?.google) return null;
  return (
    <>
      <GoogleButton />
      <div
        className="flex items-center gap-3 text-muted-foreground"
        aria-hidden="true"
      >
        <span className="h-px flex-1 bg-border" />
        or
        <span className="h-px flex-1 bg-border" />
      </div>
    </>
  );
}

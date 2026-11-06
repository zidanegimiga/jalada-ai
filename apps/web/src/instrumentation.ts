import * as Sentry from "@sentry/nextjs";

import { errorTrackingOptions } from "@/lib/error-tracking";

export function register() {
  if (process.env.NEXT_RUNTIME === "nodejs")
    Sentry.init(errorTrackingOptions());
}

/** Errors thrown while rendering on the server or in route handlers. */
export const onRequestError = Sentry.captureRequestError;

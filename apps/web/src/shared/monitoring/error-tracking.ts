import type { BrowserOptions, ErrorEvent } from "@sentry/nextjs";

/** "https://x.example/a/b?q=1#h" as "https://x.example/a/b". Query strings can hold ids. */
export function withoutQuery(url: string): string {
  const cut = url.search(/[?#]/);
  return cut === -1 ? url : url.slice(0, cut);
}

/** Takes out anything that could be personal before an error leaves the device or server. */
export function scrubEvent(event: ErrorEvent): ErrorEvent {
  delete event.user;
  if (event.request) {
    event.request = {
      method: event.request.method,
      url: event.request.url ? withoutQuery(event.request.url) : undefined,
    };
  }
  for (const crumb of event.breadcrumbs ?? []) {
    const url = crumb.data?.url;
    if (typeof url === "string")
      crumb.data = { ...crumb.data, url: withoutQuery(url) };
    if (typeof crumb.data?.to === "string")
      crumb.data = { ...crumb.data, to: withoutQuery(crumb.data.to) };
    if (typeof crumb.data?.from === "string")
      crumb.data = { ...crumb.data, from: withoutQuery(crumb.data.from) };
  }
  return event;
}

/** Shared settings for the browser and the server. Off unless a DSN was set at build time. */
export function errorTrackingOptions(): BrowserOptions {
  return {
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    enabled: Boolean(process.env.NEXT_PUBLIC_SENTRY_DSN),
    environment: process.env.APP_ENVIRONMENT,
    release: process.env.APP_VERSION,
    // Nothing about the person or their requests: the defaults would send all of these.
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpHeaders: false,
      httpBodies: [],
      urlQueryParams: false,
      databaseQueryData: false,
      stackFrameVariables: false,
    },
    // Errors only. Tracing is a separate decision.
    tracesSampleRate: 0,
    beforeSend: scrubEvent,
    // Console messages can repeat whatever a library chose to print.
    beforeBreadcrumb: (crumb) => (crumb.category === "console" ? null : crumb),
  };
}

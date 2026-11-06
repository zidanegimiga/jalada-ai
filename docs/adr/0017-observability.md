# 0017. Logs, traces and errors

Status: Accepted
Date: 2026-11-05

## Context
Every log line needs a request id, every model call needs tracing, and every pipeline run needs its tokens, cost, attempts, duration and outcome. Raw financial content must never reach logs.

## Options considered
1. **Standard logging with JSON formatting.** No dependency, but awkward to add context such as request ids.
2. **structlog.** Structured JSON logs with context that follows a request, and processors that can strip sensitive fields.

For tracing, **OpenTelemetry** is the vendor-neutral standard. For model calls, **Langfuse** (self-hosted or free tier) reads OpenTelemetry traces and shows prompts, tokens and costs. For errors, **Sentry**'s free developer tier.

## Decision
structlog for JSON logs with a request id bound per request and per job, OpenTelemetry tracing across the API, the worker and every model call, Langfuse for model traces, and Sentry for errors. A log processor drops known sensitive fields, and Sentry is configured not to send request bodies.

## Consequences
- Pipeline run records in the database are the source for run metrics. Traces are for debugging.
- Langfuse sees prompts, so it gets the same rule as model providers: real user data only under terms that keep it private, or self-hosted.

## In place
- **Logs (November 2026).** Code keeps using the standard `logging` module; structlog formats every record, including uvicorn's. Production writes one JSON object per line, local runs write readable lines. Each request gets an id from `X-Request-ID` (kept only if it looks like an id) or a new one, returned in the response and added to every line written while the request runs. Each request also gets one line with the method, the route pattern rather than the address, the status, the time taken and the user id. Jobs add their id and kind the same way. Fields that can hold personal or financial details are replaced with `[removed]`, and exceptions are written as their type and stack frames without their message, because messages can repeat what caused them.
- **Errors (November 2026).** Sentry receives crashes in requests and every job failure logged at error level, from the API and the worker, once `JALADA_SENTRY_DSN` is set. Before anything is sent, the request is cut down to its method and address without the query string; exception messages, the user, local variables and personal fields are removed; and outgoing call addresses in breadcrumbs keep only the host, because Telegram's carry the bot token. Release and environment come from the version and environment settings. Tracing is not switched on yet.
- **Web app errors (November 2026).** `@sentry/nextjs` reports errors in the browser, in server rendering and in the global error screen, once `NEXT_PUBLIC_SENTRY_DSN` is set on the web host before the build. Nothing about the person or their requests is collected: user, cookies, headers, bodies and query strings are off, click and console breadcrumbs are dropped, and addresses keep only their path. Source maps are not uploaded yet, so browser stack traces stay minified.

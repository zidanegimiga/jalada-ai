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

# 0019. Run the worker inside the API on free hosting

Status: Accepted
Date: 2026-11-05

## Context
Evidence is processed by a worker that claims jobs from Postgres (decision 0010). Render's free plan only covers web services: background workers are paid. Free web services also stop after 15 minutes with no requests and start again on the next one.

## Options considered
1. **A paid background worker.** The clean split, but a monthly cost before there are users.
2. **A scheduled job that wakes the worker.** Cron jobs are not free on Render either.
3. **The same job loop on a thread inside the API process.** Free. Jobs are queued by requests, so the API is awake when work arrives and stays awake for 15 minutes after the last request, which is far longer than a job takes.

## Decision
Option 3, switched on with `JALADA_RUN_WORKER_IN_API=true`. The loop is the worker's own (`work_until`, built by `build_job_runner` in the composition root), started and stopped with the API's lifespan. Locally and on paid hosting the separate worker keeps running and the setting stays off.

## Consequences
- One free service runs both. A slow job shares the API's memory and CPU, which is fine at this size.
- If the service sleeps with jobs still queued, they run as soon as the next request wakes it.
- A failure outside a job, such as the database being unreachable, is logged and retried rather than stopping the loop.
- Moving to a paid worker later is a setting change and a second service, with no code change.

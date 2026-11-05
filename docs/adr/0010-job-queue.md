# 0010. A job queue in Postgres

Status: Accepted
Date: 2026-11-05

## Context
Processing evidence takes seconds to minutes, so it runs in the worker, not in the request. Free hosting makes every extra service a cost or a limit.

## Options considered
1. **Celery with Redis or RabbitMQ.** Mature, but two more services to run and host.
2. **A managed queue such as Amazon SQS.** No servers, but a paid cloud dependency.
3. **A `jobs` table in Postgres.** Workers claim jobs with `SELECT ... FOR UPDATE SKIP LOCKED`. No new service, and a job is written in the same transaction as its evidence, so neither can exist without the other.

## Decision
A `jobs` table in Postgres behind a `JobQueue` port. Claims set a `locked_until` time, so a crashed worker's job is picked up again. Retries back off by pushing `run_after` forward.

## Consequences
- No extra infrastructure, and enqueueing is transactional.
- Throughput is lower than a dedicated broker, which is fine at this scale.
- Swapping to Celery later means one new adapter for the port.

# 0009. PostgreSQL with SQLAlchemy and Alembic

Status: Accepted
Date: 2026-11-05

## Context
The ledger, evidence records, pipeline traces and the job queue need a reliable relational store with transactions, unique constraints for duplicate detection, and JSON columns for step traces. It must run in Docker locally and on a free hosted tier.

## Options considered
1. **SQLite.** No server, but weak for concurrent writes from the API and the worker, and no free managed hosting.
2. **MongoDB.** Flexible documents, but money and duplicate rules want real constraints and transactions.
3. **PostgreSQL.** Strong constraints, transactions, `jsonb`, and `SKIP LOCKED` for a job queue. Free hosted tiers on Neon and Supabase.

For data access:
1. **Raw SQL with psycopg.** Full control, but every mapping is hand-written.
2. **SQLAlchemy 2.** Typed models, parameterised queries by default, and works well with mypy. Alembic, from the same authors, handles migrations.
3. **SQLModel or an ORM tied to the framework.** Mixes API schemas with database models, which works against keeping the domain separate.

## Decision
PostgreSQL 17, accessed through SQLAlchemy 2 with the psycopg 3 driver, and migrations with Alembic. SQLAlchemy models live in `adapters/`. The domain has its own plain classes and never imports SQLAlchemy.

## Consequences
- Every query is parameterised by SQLAlchemy, which closes off SQL injection.
- Mapping between domain classes and database models is extra code, in exchange for a domain that can be tested without a database.
- Integration tests run against real Postgres in Docker, not SQLite, so constraints behave as in production.

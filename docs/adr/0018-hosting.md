# 0018. Free hosting

Status: Proposed
Date: 2026-11-05

## Context
The first version should cost nothing to host while staying easy to move.

## Options considered
- **Web app:** Vercel's hobby tier (built for Next.js) or Netlify.
- **API and worker:** Render or Koyeb free tiers, which run Docker images. Free instances sleep when idle, so the first request after a pause is slow.
- **Database:** Neon or Supabase free tier Postgres.
- **Evidence:** Cloudflare R2 free tier.
- **Later:** Amazon ECS on Fargate, with RDS and S3, when the free tiers run out.

## Decision
Vercel for the web app, Render for the API and worker, Neon for Postgres and R2 for evidence. Final choice is made when deploying, since free tier terms change often.

## Consequences
- The worker on a sleeping free instance cannot poll. The API wakes it, or the worker runs inside the API process on free hosting, which the composition root allows.
- Everything is Docker and environment variables, so moving to paid hosting is configuration, not code.

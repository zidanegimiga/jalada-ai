# 0018. Free hosting

Status: Accepted
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
Netlify (Free) for the web app, Render (Free, Frankfurt) for the API with the job loop inside it (decision 0019), Neon (Free, AWS Frankfurt) for Postgres, and Cloudflare R2 for evidence. The API service is described in `render.yaml`, the web app in `netlify.toml`, and every production setting in `.env.production.example`.

## Consequences
- Render's free plan has no background workers or pre-deploy step, so the job loop runs inside the API and migrations run when it starts.
- Free Render services sleep after 15 minutes without requests and take about a minute to wake.
- Netlify's free plan has monthly build and bandwidth limits. Check its terms before the app charges anyone.
- Netlify gives up on a forwarded request after about 26 seconds, so the first action after the API has been asleep can fail and need a retry.
- Everything is Docker and environment variables, so moving to paid hosting is configuration, not code.

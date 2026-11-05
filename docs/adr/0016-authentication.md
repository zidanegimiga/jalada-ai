# 0016. Authentication: our own sessions, Argon2 and Google

Status: Accepted
Date: 2026-11-05

## Context
Users sign in with email and password or with Google. Sessions must live in secure, HTTP-only cookies. Every query is scoped to the signed-in user.

## Options considered
1. **A hosted auth service such as Clerk, Auth0 or Supabase Auth.** Fast, but user records live with a third party, free tiers have limits, and it adds a vendor for personal data.
2. **JSON Web Tokens in cookies.** No session table, but tokens cannot be revoked before they expire.
3. **Our own server-side sessions.** A random token in an HTTP-only cookie, only its hash stored in Postgres. Revoking is deleting a row.

For passwords, **Argon2id** through `argon2-cffi`, the current recommendation of the Open Worldwide Application Security Project (OWASP). For Google, **Authlib** for the OpenID Connect sign-in flow.

## Decision
Server-side sessions in Postgres, Argon2id password hashes, and Google sign-in with Authlib. A FastAPI dependency resolves the session to a user id, and repositories take that id on every call. Sign-in and sign-up are rate limited with slowapi.

## Consequences
- We own the security of sign-in, so it needs careful tests, including timing-safe comparisons and lockout.
- Password reset needs email sending, which is a later decision. Until then, Google sign-in covers forgotten passwords.

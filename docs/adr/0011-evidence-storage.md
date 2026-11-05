# 0011. Evidence storage: S3-compatible, encrypted by the app

Status: Accepted
Date: 2026-11-05

## Context
Receipts, PDFs and pasted messages are kept permanently as evidence. They are personal financial data, must be encrypted at rest, and must only be served through short-lived links.

## Options considered
1. **Files in Postgres.** One store, but it bloats the database and backups.
2. **Local disk.** Simple, but free hosts have no persistent disk.
3. **S3-compatible object storage.** SeaweedFS locally, Cloudflare R2 when hosted (10 GB free and no egress fees), Amazon S3 later. One client library, boto3, talks to all three.

For local storage, MinIO was the first choice, but it stopped publishing Docker images for its community edition in late 2025. SeaweedFS is Apache licensed, actively released, and speaks the same S3 API.

For encryption:
1. **Rely on the provider's encryption at rest.** Easy, but the provider can read the files.
2. **Encrypt in the app before upload.** AES-GCM with a key from settings, using the `cryptography` library. The storage provider only ever sees ciphertext.

## Decision
An `EvidenceStore` port with an S3 adapter on boto3, used with SeaweedFS in docker compose and R2 when hosted. Files are encrypted with AES-256-GCM in the app before upload, with a fresh nonce per object, and the ciphertext is bound to its object name so it cannot be swapped with another. Downloads go through the API, which checks that the evidence belongs to the signed-in user, then decrypts it and sends it with `Cache-Control: private, no-store`. Short-lived signed links come later, for places that need a link without a session, such as Telegram replies.

## Consequences
- Losing the encryption key means losing the evidence, so the key needs a backup outside the host.
- The API does the decryption, so evidence downloads pass through it rather than straight from the bucket.
- Each evidence row stores the id of the key that encrypted it. `JALADA_EVIDENCE_KEYS` takes several keys: the first encrypts, the rest still decrypt, so keys can be rotated without re-encrypting everything at once.
- Files are checked by their first bytes (JPEG, PNG, WebP or PDF), never by name or declared type, and are limited to 10 MB.

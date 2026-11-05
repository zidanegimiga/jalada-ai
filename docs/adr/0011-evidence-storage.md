# 0011. Evidence storage: S3-compatible, encrypted by the app

Status: Accepted
Date: 2026-11-05

## Context
Receipts, PDFs and pasted messages are kept permanently as evidence. They are personal financial data, must be encrypted at rest, and must only be served through short-lived links.

## Options considered
1. **Files in Postgres.** One store, but it bloats the database and backups.
2. **Local disk.** Simple, but free hosts have no persistent disk.
3. **S3-compatible object storage.** MinIO locally, Cloudflare R2 when hosted (10 GB free and no egress fees), Amazon S3 later. One client library, boto3, talks to all three.

For encryption:
1. **Rely on the provider's encryption at rest.** Easy, but the provider can read the files.
2. **Encrypt in the app before upload.** AES-GCM with a key from settings, using the `cryptography` library. The storage provider only ever sees ciphertext.

## Decision
An `EvidenceStore` port with an S3 adapter on boto3, used with MinIO in docker compose and R2 when hosted. Files are encrypted with AES-GCM in the app before upload. Downloads go through the API, which checks ownership, then decrypts and streams the file, or issues a five-minute signed link to an endpoint that does.

## Consequences
- Losing the encryption key means losing the evidence, so the key needs a backup outside the host.
- The API does the decryption, so evidence downloads pass through it rather than straight from the bucket.
- Key rotation needs a stored key id per object, which is included from the start.

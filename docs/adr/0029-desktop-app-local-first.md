# 0029. A desktop app that works offline

Status: Accepted
Date: 2026-11-20
Builds on: 0011 (evidence encryption), 0020 (feature modules), 0024 (web app layout), 0028 (installable web app)

## Context
People keep money records in bursts: an evening with a pile of receipts, or a month of M-Pesa messages at once. Connections in Kenya drop often, and data bundles run out. The installable web app (0028) shows a clear offline page, but nothing can be read or added without a connection.

A desktop app should keep working offline: show the ledger, take new evidence and confirm entries, then send everything when the connection returns. That raises problems the web app never had:

- **Records on the device.** Financial records are personal data. A copy on a laptop must be protected if the laptop is lost or shared.
- **Changes made offline.** Each change must survive the app closing, reach the server exactly once, and in the right order.
- **Knowing what is real.** People must be able to tell a change only saved on their device from one the server has accepted, since only the server's copy counts at filing time (AGENTS.md: the database is the source of truth).
- **Conflicts.** The same entry can change on the phone while the laptop is offline.
- **Sign-in.** Passkeys and security keys should work on the desktop as they will on the web and Android.
- **Attack surface.** A desktop app runs with the user's file access. It must load nothing it did not ship and talk to no server but ours.

## Options considered
**Shell.**
1. *Electron.* Chromium and Node.js, the same engine on every system, so the app behaves the same on Windows, macOS and Linux. Larger download (about 100 MB) and more memory.
2. *Tauri.* Smaller, using the system's web view, but each system's web view behaves differently, and the native side is Rust, a second language to maintain.

**What the window shows.**
1. *The hosted web app, with a separate offline screen.* Two interfaces, and the offline one always lags behind.
2. *A local-first interface.* The window always reads from the local database and writes through a queue; a sync engine talks to the API in the background. One interface, the same online and offline.

**Local database.**
1. *IndexedDB in the window.* Built in, but not encrypted, and hard to query.
2. *SQLite in the main process, encrypted with SQLCipher* through `better-sqlite3-multiple-ciphers`. Real queries and transactions, one file, encrypted at rest.

## Decision
**Electron, with a local-first interface over encrypted SQLite.** The code lives in `apps/desktop`.

**Processes.** The main process owns the database, the sync engine and all network access. The window is a React app built with Vite. It runs sandboxed, with context isolation on and Node.js off, and reaches the main process only through a small, typed bridge (`preload`). The bridge offers named calls such as `ledger.list` and `changes.capture`, never raw SQL or raw requests.

**Local data.** One SQLite file per signed-in person, encrypted with SQLCipher. A random 256-bit key is made on first use and stored with Electron's `safeStorage`, which uses the Keychain on macOS, DPAPI on Windows and the Secret Service on Linux. Signing out deletes the file and the key.

**Changes as a queue.** Every change the person makes is written in one local transaction: to the local records, so the screen updates at once, and to a `changes` table, in order, with its own id. Each change has a state the interface shows:

| State | Meaning |
|---|---|
| Saved on this device | In the queue, not yet sent. |
| Sending | On its way to the server. |
| Confirmed | Accepted by the server; the local record now holds the server's copy. |
| Needs attention | Refused, or in conflict; waits for the person. |

**Sync.** When the connection returns, or every few minutes while online, the engine:
1. Sends queued changes in order. Each request carries an `Idempotency-Key`, the change's id, so a change retried after a dropped reply is applied once.
2. Pulls what changed on the server since its last cursor, from a change feed, and updates the local records.

**Conflicts.** Entries get a version number on the server. An edit is sent with the version it was based on. If the server's copy has moved on, the API answers 409 with its current copy. The change becomes *Needs attention*, and the person sees both and picks one. Nothing is merged silently, since these are financial records.

**Server changes this needs**, each its own slice:
- An `Idempotency-Key` header on the write routes the desktop uses, with results kept for 24 hours.
- A `version` on entries, checked on edits and confirmations.
- `GET /v1/sync/entries?after=` returning every entry saved since a position, in any state, with the position to ask from next time. Each save records the database transaction that made it, and the feed only returns saves from transactions that have finished. A save still in progress is returned on a later read, never skipped, which ordering by a counter or a clock could not promise. Nothing is deleted on the server, so the feed has no deletions: an entry that leaves the ledger arrives with its new status.

**Sign-in.** The desktop app signs in through the system browser, as recommended for native apps (RFC 8252), and receives a device session through a `jalada://` link. That way passkeys, security keys and Google sign-in all work exactly as on the web, with the system's own prompts. WebAuthn itself gets its own decision.

**Traffic.** The main process cancels every request that is not to the app's own files or the configured API origin, and the window has a strict Content Security Policy (CSP). Navigation away from the app and new windows are refused, and permission requests (camera, location and so on) are denied by default.

**Dependencies.** Every dependency is pinned by the lockfile. CI runs `npm audit` and a licence check, and a short list in the repository records why each runtime dependency is there.

**Performance.** The window shows the last known ledger straight from SQLite, before any network call. A start-up test in CI fails if the first screen takes longer than its budget.

## Consequences
- People can read their records, add evidence and confirm entries without a connection, and always see which changes the server has accepted.
- The API gains idempotency keys, entry versions and a change feed. The web app and Telegram benefit from the first two as well.
- The desktop interface is a second React app. Building blocks are shared with the web app where they have no Next.js parts; anything shared by both moves to a package later, rather than being copied.
- Installers are unsigned at first, so systems will warn before opening them. Signing (an Apple developer account, a Windows certificate) comes before any public release.
- Records on the device are only as safe as the device's own sign-in. The app says so where it explains offline use.

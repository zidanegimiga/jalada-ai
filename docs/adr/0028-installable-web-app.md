# 0028. An installable web app

Status: Accepted
Date: 2026-11-20
Builds on: 0005 (frontend toolchain), 0024 (web app layout)

## Context
Most people use Jalada AI on a phone, often with patchy data. Today it only lives in a browser tab: there is nothing to put on the home screen, every visit downloads the app's code again, and losing the connection shows the browser's own error page.

A web app can be installed when it has a manifest and a service worker (a script the browser runs between the page and the network). The service worker also decides what is kept on the device, which matters here: the app holds financial records, which are personal data under the Data Protection Act, 2019.

Working fully offline, with records kept and changed on the device and synchronised later, is a separate decision for the desktop app.

## Options considered
1. **A library such as Serwist or Workbox.** Ready-made caching strategies and precaching, but another build plugin and dependency tree to review and keep up to date, for a handful of rules.
2. **A service worker written by hand, served by a route.** A short script with three rules. No new dependency. The route stamps each build's version into it, so browsers notice new builds.
3. **No service worker, only a manifest.** Installable on some browsers, but no offline page and no faster start.

## Decision
Option 2. `app/sw.js/route.ts` serves the script built by `features/offline/service-worker.ts`.

What it does:
- **Build files** (`/_next/static/`, icons) are served from the device first. Their names change with their content, so they never go stale, and repeat visits start without downloading them.
- **Pages** come from the network. Public pages (the landing page, sign-in, sign-up, the privacy notice) are kept as a fallback. Any other page, when the network fails, shows `/offline`, which reloads itself when the connection returns.
- **Everything else is left alone:** `/v1` calls, any request that is not a GET, and any other website. Records, receipts and signed-in pages are never stored by the service worker, so nothing personal is left on a shared phone.
- **Updates wait for the person.** A new version installs in the background and the app offers to reload, rather than swapping code under a half-filled form.

The manifest is `app/manifest.ts`, with icons in `public/icons/`, including maskable ones that Android crops to its own shape.

## Consequences
- The app can be installed from Chrome, Edge and Samsung Internet, and added to the home screen from Safari, which has no install prompt; the Account page explains how.
- Repeat visits start faster, since the code is already on the device.
- Without a connection people see a clear offline page instead of a browser error, but they cannot read or add records offline in the web app.
- The service worker runs in production builds only, so development reloads are never served stale code.

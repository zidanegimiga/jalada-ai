# 0005. Frontend toolchain

Status: Accepted
Date: 2026-11-05

## Context
The web app is where users upload evidence, review proposed entries and read their ledger. Most users are on small, low-cost Android phones with slow or expensive data, so pages must be light and fast on first load. The app talks to the FastAPI backend through a typed client generated from its OpenAPI schema.

## Options considered

### Framework
1. **Plain React with Vite.** Small and simple, but everything renders in the browser, so a slow phone downloads and runs all the JavaScript before showing anything. Routing and data loading are ours to build.
2. **Remix (now React Router).** Server rendering and good form handling. A smaller ecosystem, and fewer free hosts tuned for it.
3. **Next.js with the App Router.** Server components send finished HTML and keep most code off the phone. Routing, image optimisation and font self-hosting are built in. Free hosting on Vercel's hobby tier.

### Language
1. **JavaScript.** Less setup.
2. **TypeScript.** Catches mistakes before they run, and the generated API client gives typed requests and responses for free.

### Styling
1. **CSS modules.** Scoped styles, but every component needs its own file and naming.
2. **A component kit such as Material UI.** Fast to start, but heavy to download, and every app built with it looks the same.
3. **Tailwind CSS.** Utility classes in the markup. Only the classes actually used are shipped, which keeps the stylesheet small.

### Linting
**ESLint** with Next.js's own rules, including its Core Web Vitals checks (Google's page speed and stability measures). There is no serious alternative with Next.js rules.

### Tests
1. **Jest.** Mature, but needs extra setup for TypeScript and modern modules.
2. **Vitest with Testing Library.** Fast, works with TypeScript out of the box, and uses the same API as Jest. Testing Library checks components the way a user sees them, by text and role, not by internal details.

End-to-end tests of whole journeys will use Playwright, recorded here so the choice is in one place.

### Package manager
1. **pnpm.** Faster installs and less disk space.
2. **npm.** Comes with Node, needs no extra install on any machine or build host, and `npm audit` is built in.

## Decision
Next.js with the App Router, TypeScript in strict mode, Tailwind CSS, ESLint with the Next.js rules, Vitest with Testing Library, Playwright for journeys, and npm.

## Consequences
- Pages render on the server by default. Code only reaches the phone when a component is marked as a client component, so that marker should be used sparingly.
- Next.js changes quickly between major versions. The lockfile pins it and upgrades are deliberate.
- Vitest cannot render async server components. Those are tested through Playwright instead.

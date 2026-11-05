# 0007. Continuous integration on GitHub Actions

Status: Accepted
Date: 2026-11-05

## Context
Every pull request should prove that the code lints, type checks and passes its tests, that no dependency has a known vulnerability, and that no secret has slipped into the history. The code lives on GitHub, and the checks must be free for a public or personal repository.

## Options considered

### Runner
1. **GitHub Actions.** Built into GitHub, free minutes for personal repositories, and official actions exist for uv, Node and gitleaks.
2. **CircleCI or GitLab CI.** Capable, but a second service to connect and pay attention to.

### Python dependency audit
1. **pip-audit.** Checks packages against the Python Packaging Advisory Database. It reads a requirements file exported from `uv.lock`, so it audits exactly what ships.
2. **Safety.** The free tier's database is delayed and the tool now needs an account.

### Python security lint
1. **Bandit as its own tool.** Another install and configuration.
2. **Bandit's rules through ruff.** Ruff's `S` rules are a port of Bandit's checks and already run on every lint, locally and in CI.

### Secret scanning
1. **GitHub's built-in secret scanning.** Only for known token formats, and push protection is not on every plan.
2. **gitleaks.** Scans every commit for keys, tokens and high-entropy strings, and runs the same way locally.

### Dependency updates
1. **Renovate.** Very configurable, but an extra app to install.
2. **Dependabot.** Built into GitHub, and supports uv, npm, Docker and GitHub Actions.

## Decision
GitHub Actions with three workflows: one for Python, one for the web app, and one for secrets. Each language workflow only runs when its files change. Python uses ruff (including Bandit's rules), mypy, pytest and pip-audit. The web app uses ESLint, the TypeScript compiler, Vitest and `npm audit --omit=dev`. gitleaks scans the full history. Dependabot opens weekly update pull requests.

## Consequences
- `npm audit` only fails on packages that ship to users. Advisories in development tools, such as ESLint plugins, are handled by Dependabot updates instead of blocking every pull request.
- Bandit's rules live in ruff, so a security finding shows up in the editor, not only in CI.
- Evaluation runs and Docker image builds join CI once there is something for them to check.

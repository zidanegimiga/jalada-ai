# 0006. Docker images and docker compose

Status: Accepted
Date: 2026-11-05

## Context
The API, the worker and the web app must run the same way on local environments, in continuous integration and on virtual machines. The whole stack, including Postgres and object storage, should start locally with one command.

## Options considered

### Packaging
1. **No containers.** Run each app with uv and npm directly, and install Postgres on each machine. Less to learn, but every machine drifts, and hosts each need their own build setup.
2. **Docker images, one per app.** The same image runs everywhere. Every free backend host we are considering accepts a Dockerfile.

### Base images
1. **Alpine.** Very small, but it uses musl instead of glibc, so many Python packages with compiled parts (for example image and PDF libraries) have no prebuilt wheels and must compile during the build.
2. **Debian slim (trixie).** A little larger, but prebuilt wheels work and the build stays fast.
3. **Distroless.** Smallest attack surface, but no shell, which makes debugging hard while the project is young.

### Local orchestration
1. **docker compose.** Ships with Docker and describes every service in one file.
2. **A local Kubernetes cluster, such as kind or minikube.** Closer to large production setups, but far more than this project needs.

## Decision
One Docker image per app, built in stages so build tools never reach the final image, on Debian slim base images, running as a non-root user. The Python images are built from the repo root so they can use the shared `uv.lock`. The web image uses Next.js standalone output, which copies in only the files the server needs. docker compose runs the whole stack locally.

## Consequences
- Builds need network access for packages and for the web font, which Next.js downloads and self-hosts at build time.
- Python images install exactly what `uv.lock` pins, with no development tools.
- Changing a base image version is a one-line edit, and Dependabot can propose it.
- If a host needs something other than a Dockerfile, the image still documents exactly how the app runs.

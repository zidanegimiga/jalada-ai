# Build from the repo root: docker build -f apps/api/Dockerfile .
FROM ghcr.io/astral-sh/uv:0.13-python3.12-trixie-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Install third-party packages first, so this layer is reused when only our code changes.
COPY pyproject.toml uv.lock .python-version ./
COPY apps/api/pyproject.toml apps/api/
COPY apps/worker/pyproject.toml apps/worker/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package jalada --no-install-workspace

COPY apps/api apps/api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package jalada --no-editable

FROM python:3.15-slim-trixie
# Tesseract reads receipt photos when the job loop runs inside the API (decision 0019).
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --no-create-home jalada
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER jalada
EXPOSE 8000
CMD ["jalada-serve"]

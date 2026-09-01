# syntax=docker/dockerfile:1
# dhi.io/python:3.13-debian13-dev — digest pinned (DOCKER-BUILD-003)
# Refresh digests: docker login dhi.io && bash scripts/pin-dhi-digests.sh
FROM dhi.io/python:3.14-debian13-dev@sha256:58fa6507f5442f3426b82f70cc89d7c547fd14a5a0ecdc429da8021133b49323 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Dependency layer (cache-friendly)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-editable

# Project layer — non-editable so runtime needs only .venv (DOCKER-BUILD-001)
COPY src ./src
COPY README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Runtime — DHI Community minimal Python (no shell / package manager)
# dhi.io/python:3.13-debian13 — digest pinned (DOCKER-BUILD-003)
FROM dhi.io/python:3.14-debian13@sha256:eeea2a4fbc5a741c557a9fea827d55753dda653672811ed9b9ffcf4f5a137697 AS runtime
ARG VERSION=0.0.0
ARG REVISION=unknown
ARG SOURCE=https://github.com/pirlruc/gitlab-mcp

LABEL org.opencontainers.image.title="gitlab-mcp" \
      org.opencontainers.image.description="MCP server for GitLab merge request tools (stdio)" \
      org.opencontainers.image.source="${SOURCE}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# DHI runtime defaults to nonroot 65532:65532 (DOCKER-RUN-001) — no useradd on runtime.
COPY --from=builder --chown=65532:65532 /app/.venv /app/.venv

USER 65532:65532
WORKDIR /app

# Stdio MCP — no EXPOSE, no HEALTHCHECK (DOCKER-RUN-006); documented in docs/docker.md
ENTRYPOINT ["gitlab-mcp"]

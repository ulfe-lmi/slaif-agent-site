# Python 3.12.12; PSF license; multi-platform official image.
FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c AS builder
# uv 0.12.5; Apache-2.0 OR MIT; multi-platform official image.
COPY --from=ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /build
COPY pyproject.toml uv.lock README.md LICENSE NOTICE alembic.ini ./
COPY migrations ./migrations
COPY services/backend/src ./services/backend/src
RUN uv sync --frozen --no-default-groups --no-editable

# Keep the readable version beside the immutable top-level multi-architecture digest.
FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c AS runtime
RUN groupadd --gid 10001 slaif \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin slaif
ENV PATH=/opt/slaif/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /opt/slaif
COPY --from=builder --chown=10001:10001 /build/.venv ./.venv
COPY --chown=10001:10001 alembic.ini ./
COPY --chown=10001:10001 migrations ./migrations
COPY --chown=10001:10001 tools/local_secrets/initialize.py ./bin/initialize-local-secrets.py
USER 10001:10001
CMD ["python", "-m", "slaif_agent_site.control_api"]

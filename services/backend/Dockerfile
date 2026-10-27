# Python 3.12.15; PSF license; multi-platform official image.
FROM python:3.12.15-alpine3.23@sha256:1fd55c2f838c4f76262f9eeed899ff9168ea96ac383c61667d6f204325e1f169 AS builder
ARG SOURCE_DATE_EPOCH=1704067200
# uv 0.12.5; Apache-2.0 OR MIT; multi-platform official image.
COPY --from=ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 /uv /uvx /bin/
RUN apk --timeout 30 add --no-cache 'libcrypto3=3.5.9-r0' 'libssl3=3.5.9-r0'

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /build
COPY pyproject.toml uv.lock README.md LICENSE NOTICE alembic.ini ./
COPY migrations ./migrations
COPY services/backend/src ./services/backend/src
RUN uv sync --frozen --no-default-groups --no-editable \
    && set -- .venv/lib/python3.12/site-packages/slaif_agent_site-*.dist-info \
    && [ "$#" -eq 1 ] \
    && [ -f "$1/uv_cache.json" ] \
    && rm -- "$1/uv_cache.json" \
    && sed -i '\|slaif_agent_site-.*\.dist-info/uv_cache\.json,|d' "$1/RECORD"
RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib

# Keep the readable version beside the immutable top-level multi-architecture digest.
FROM python:3.12.15-alpine3.23@sha256:1fd55c2f838c4f76262f9eeed899ff9168ea96ac383c61667d6f204325e1f169 AS runtime
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site backend" \
      org.opencontainers.image.description="Shared backend process image for the SLAIF Agent-Site deployment skeleton" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
RUN apk --timeout 30 add --no-cache 'libcrypto3=3.5.9-r0' 'libssl3=3.5.9-r0' \
    && addgroup -g 10001 -S slaif \
    && adduser -u 10001 -S -D -H -h /nonexistent -s /sbin/nologin -G slaif slaif
# 083-7-a: remove the measured unnecessary system pip installer copies from the
# runtime image only: pip package + distribution metadata, ensurepip bootstrap
# wheel, and pip command links/scripts. Builder, base, interpreter, stdlib and
# the app venv are unchanged; the ensurepip module itself is retained.
RUN rm -r -- /usr/local/lib/python3.12/site-packages/pip \
    /usr/local/lib/python3.12/site-packages/pip-25.0.1.dist-info \
    && rm -- /usr/local/lib/python3.12/ensurepip/_bundled/pip-25.0.1-py3-none-any.whl \
    && rm -- /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.12
ENV PATH=/opt/slaif/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /opt/slaif
COPY --from=builder --chown=10001:10001 /build/.venv ./.venv
COPY --chown=10001:10001 alembic.ini ./
COPY --chown=10001:10001 migrations ./migrations
COPY --chown=10001:10001 tools/local_secrets/initialize.py ./bin/initialize-local-secrets.py
USER 10001:10001
CMD ["python", "-m", "slaif_agent_site.control_api"]

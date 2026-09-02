# PostgreSQL 18.6 official Alpine base; Alpine aports OpenSSL source commit
# 2b4b2590f782b95276d31dcaaf41554b1a597a0b supplies the exact fixed packages.
FROM docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f

ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0

LABEL org.opencontainers.image.title="SLAIF Agent-Site PostgreSQL security overlay" \
      org.opencontainers.image.description="PostgreSQL 18.6 official Alpine runtime with the exact OpenSSL security overlay" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="PostgreSQL" \
      org.opencontainers.image.version="$SLAIF_IMAGE_VERSION" \
      org.opencontainers.image.revision="$SLAIF_IMAGE_REVISION" \
      org.opencontainers.image.created="$SLAIF_IMAGE_CREATED"

RUN apk add --no-cache \
      --repository=https://dl-cdn.alpinelinux.org/alpine/v3.23/main \
      'libcrypto3=3.5.8-r0' \
      'libssl3=3.5.8-r0' \
    && test "$(awk '/^P:libcrypto3$/{found=1} found && /^V:/{print substr($0,3); exit}' /lib/apk/db/installed)" = "3.5.8-r0" \
    && test "$(awk '/^P:libssl3$/{found=1} found && /^V:/{print substr($0,3); exit}' /lib/apk/db/installed)" = "3.5.8-r0"

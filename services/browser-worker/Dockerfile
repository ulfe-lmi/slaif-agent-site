# Node.js 24.14.1; MIT license; official multi-platform image.
# This placeholder has no production package dependency: Node executes its
# erasable TypeScript directly after the frozen workspace type-check gate.
FROM node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site browser worker" \
      org.opencontainers.image.description="Health-only browser worker placeholder for the SLAIF Agent-Site deployment skeleton" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
ENV BROWSER_WORKER_HOST=0.0.0.0 \
    BROWSER_WORKER_PORT=3100 \
    NODE_ENV=production \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /opt/slaif
RUN apk --timeout 30 add --no-cache 'libcrypto3=3.5.7-r0' 'libssl3=3.5.7-r0' \
    && find /usr/local/lib/node_modules/npm -depth -delete \
    && rm /usr/local/bin/npm /usr/local/bin/npx \
    && addgroup -g 10001 -S slaif \
    && adduser -u 10001 -S -D -H -h /nonexistent -s /sbin/nologin -G slaif slaif
COPY --chown=10001:10001 services/browser-worker/package.json ./package.json
COPY --chown=10001:10001 services/browser-worker/src ./src
USER 10001:10001
EXPOSE 3100
CMD ["node", "src/server.ts"]

# Node.js 24.14.1; MIT license; official multi-platform image.
FROM node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5 AS builder
ARG SOURCE_DATE_EPOCH=1704067200
ENV NEXT_TELEMETRY_DISABLED=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /build
RUN apk --timeout 30 add --no-cache 'libcrypto3=3.5.7-r0' 'libssl3=3.5.7-r0' \
    && corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json tsconfig.json ./
COPY packages ./packages
COPY apps/web ./apps/web
COPY docs/assets/slaif-logo.svg ./docs/assets/slaif-logo.svg
COPY docs/assets/slaif-logo.svg ./apps/web/public/slaif-logo.svg
RUN pnpm install --frozen-lockfile --filter @slaif-agent-site/web... \
    && pnpm --filter @slaif-agent-site/web build

# Keep the readable version beside the immutable top-level multi-architecture digest.
FROM node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5 AS runtime
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site Web" \
      org.opencontainers.image.description="Standalone Next.js status surface for the SLAIF Agent-Site deployment skeleton" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
ENV HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /opt/slaif
RUN apk --timeout 30 add --no-cache 'libcrypto3=3.5.7-r0' 'libssl3=3.5.7-r0' \
    && find /usr/local/lib/node_modules/npm -depth -delete \
    && rm /usr/local/bin/npm /usr/local/bin/npx \
    && addgroup -g 10001 -S slaif \
    && adduser -u 10001 -S -D -H -h /nonexistent -s /sbin/nologin -G slaif slaif
COPY --from=builder --chown=10001:10001 /build/apps/web/.next/standalone ./
# Next 16's standalone tracer omits unused ESM helper files even though its
# runtime export map may resolve them; restore the frozen transitive package.
COPY --from=builder --chown=10001:10001 /build/node_modules/.pnpm/@swc+helpers@0.5.23 ./node_modules/.pnpm/@swc+helpers@0.5.23
COPY --from=builder --chown=10001:10001 /build/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=10001:10001 /build/apps/web/public ./apps/web/public
USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]

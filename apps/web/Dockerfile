# Node.js 24.14.1; MIT license; official multi-platform image.
FROM node:24.14.1-bookworm-slim@sha256:b506e7321f176aae77317f99d67a24b272c1f09f1d10f1761f2773447d8da26c AS builder
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /build
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json tsconfig.json ./
COPY packages ./packages
COPY apps/web ./apps/web
COPY docs/assets/slaif-logo.svg ./apps/web/public/slaif-logo.svg
RUN pnpm install --frozen-lockfile --filter @slaif-agent-site/web... \
    && pnpm --filter @slaif-agent-site/web build

# Keep the readable version beside the immutable top-level multi-architecture digest.
FROM node:24.14.1-bookworm-slim@sha256:b506e7321f176aae77317f99d67a24b272c1f09f1d10f1761f2773447d8da26c AS runtime
ENV HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000
WORKDIR /opt/slaif
RUN groupadd --gid 10001 slaif \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin slaif
COPY --from=builder --chown=10001:10001 /build/apps/web/.next/standalone ./
# Next 16's standalone tracer omits unused ESM helper files even though its
# runtime export map may resolve them; restore the frozen transitive package.
COPY --from=builder --chown=10001:10001 /build/node_modules/.pnpm/@swc+helpers@0.5.23 ./node_modules/.pnpm/@swc+helpers@0.5.23
COPY --from=builder --chown=10001:10001 /build/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=10001:10001 /build/apps/web/public ./apps/web/public
USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]

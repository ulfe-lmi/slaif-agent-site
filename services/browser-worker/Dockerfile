# Playwright 1.62.1 Noble; Apache-2.0; official multi-platform image.
FROM mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e AS builder
ARG SOURCE_DATE_EPOCH=1704067200
ARG TARGETARCH
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /build
RUN corepack enable && corepack prepare pnpm@11.22.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json tsconfig.json ./
COPY packages ./packages
COPY services/browser-worker ./services/browser-worker
RUN test "$TARGETARCH" = amd64 \
    && curl --fail --location --retry 3 \
      --output /tmp/chrome-for-testing.zip \
      https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.64/linux64/chrome-linux64.zip \
    && echo '8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e  /tmp/chrome-for-testing.zip' \
      | sha256sum --check --strict \
    && node services/browser-worker/extract-zip.mjs \
      /tmp/chrome-for-testing.zip /chrome-for-testing \
    && test "$(/chrome-for-testing/chrome-linux64/chrome --version)" \
      = 'Google Chrome for Testing 152.0.7977.64 ' \
    && rm /tmp/chrome-for-testing.zip \
    && pnpm install --frozen-lockfile --filter @slaif-agent-site/browser-worker... \
    && pnpm --filter @slaif-agent-site/browser-tool-contracts build \
    && pnpm --filter @slaif-agent-site/browser-worker build \
    && pnpm --filter @slaif-agent-site/browser-worker deploy --prod --legacy /output \
    && rm -rf /output/node_modules/.bin /output/node_modules/.pnpm/node_modules \
    && rm -f /output/node_modules/.modules.yaml \
      /output/node_modules/.package-map.json /output/node_modules/.pnpm/lock.yaml

# Node.js 24.18.1 and compatible Chromium libraries come from the exact
# Playwright image. The builder replaces its vulnerable browser payload with
# SHA-256-verified Chrome for Testing 152.0.7977.64. No install or download runs
# after build.
FROM mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e AS runtime
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site browser worker" \
      org.opencontainers.image.description="Confined Chromium worker for private COW preview evidence" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
ENV BROWSER_WORKER_HOST=0.0.0.0 \
    BROWSER_WORKER_PORT=3100 \
    BROWSER_WORKER_CHROMIUM_EXECUTABLE=/ms-playwright/chromium-1669021/chrome-linux64/chrome \
    BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=152.0.7977.64 \
    HOME=/tmp \
    NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /opt/slaif
RUN rm -rf /ms-playwright/* /usr/lib/node_modules/npm \
    && rm -f /usr/bin/npm /usr/bin/npx /usr/bin/corepack /usr/bin/pnpm /usr/bin/pnpx \
    && groupadd --gid 10001 slaif \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent \
      --shell /usr/sbin/nologin slaif
COPY --from=builder --chown=10001:10001 /chrome-for-testing/chrome-linux64 /ms-playwright/chromium-1669021/chrome-linux64
COPY --from=builder --chown=10001:10001 /output ./
USER 10001:10001
EXPOSE 3100
CMD ["node", "dist/server.js"]

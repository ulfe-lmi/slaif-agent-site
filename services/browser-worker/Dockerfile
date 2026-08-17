# Node.js 24.14.1; MIT license; official multi-platform image.
# This placeholder has no production package dependency: Node executes its
# erasable TypeScript directly after the frozen workspace type-check gate.
FROM node:24.14.1-bookworm-slim@sha256:b506e7321f176aae77317f99d67a24b272c1f09f1d10f1761f2773447d8da26c
ENV BROWSER_WORKER_HOST=0.0.0.0 \
    BROWSER_WORKER_PORT=3100 \
    NODE_ENV=production
WORKDIR /opt/slaif
RUN groupadd --gid 10001 slaif \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin slaif
COPY --chown=10001:10001 services/browser-worker/package.json ./package.json
COPY --chown=10001:10001 services/browser-worker/src ./src
USER 10001:10001
EXPOSE 3100
CMD ["node", "src/server.ts"]

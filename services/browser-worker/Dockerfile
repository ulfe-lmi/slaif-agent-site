# Playwright 1.62.1 Noble; Apache-2.0; official multi-platform image.
FROM mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e AS builder
ARG SOURCE_DATE_EPOCH=1704067200
ARG TARGETARCH
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /build
# Before any build step, the base image's NodeSource nodejs 24.18.1 is
# purged; every APT invocation that can download packages before fixed
# APT is installed uses the command-local -o Acquire::Retries=0, and the
# first protected install fixes apt and libapt-pkg6.0t64 to 2.8.4ubuntu0.1
# (CVE-2026-109518) before the vulnerable libbrotli1 1.1.0-2build2 is
# replaced by the fixed 1.1.0-2ubuntu0.1; Node.js comes from the
# hash-pinned official 24.22.1 archive (CVE-2026-111497 fix).
RUN test "$TARGETARCH" = amd64 \
    && DEBIAN_FRONTEND=noninteractive apt-get purge -y nodejs -o Acquire::Retries=0 \
    && apt-get -o Acquire::Retries=0 update \
    && apt-get -o Acquire::Retries=0 install --no-install-recommends --yes \
      'apt=2.8.4ubuntu0.1' \
      'libapt-pkg6.0t64=2.8.4ubuntu0.1' \
    && test "$(dpkg-query -W -f='${Version}' apt)" = 2.8.4ubuntu0.1 \
    && test "$(dpkg-query -W -f='${Version}' libapt-pkg6.0t64)" = 2.8.4ubuntu0.1 \
    && apt-get -o Acquire::Retries=0 install --no-install-recommends --yes 'libbrotli1=1.1.0-2ubuntu0.1' \
    && test "$(dpkg-query -W -f='${Version}' libbrotli1)" = 1.1.0-2ubuntu0.1 \
    && curl --fail --location --retry 3 \
      --output /tmp/node-v24.22.1-linux-x64.tar.gz \
      https://nodejs.org/dist/v24.22.1/node-v24.22.1-linux-x64.tar.gz \
    && echo 'eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c  /tmp/node-v24.22.1-linux-x64.tar.gz' \
      | sha256sum --check --strict \
    && tar -xzf /tmp/node-v24.22.1-linux-x64.tar.gz -C /usr/local --strip-components=1 \
    && rm /tmp/node-v24.22.1-linux-x64.tar.gz \
    && test "$(node --version)" = v24.22.1
# 083-9-c: remove the seven unnecessary inherited Python 3.12 packages: the
# four versioned packages are catalogued 3.12.3-1ubuntu0.15 with
# CVE-2026-115557, the three defaults 3.12.3-0ubuntu2.1. The fail-closed
# simulation accepts only Purg operation rows, and only for exactly these
# seven; any other operative action is rejected; the post check proves
# known-record state and path absence.
RUN test "$TARGETARCH" = amd64 \
    && set -e \
    && LC_ALL=C DEBIAN_FRONTEND=noninteractive apt-get -s purge -y \
      python3 python3-minimal libpython3-stdlib \
      python3.12 python3.12-minimal libpython3.12-stdlib libpython3.12-minimal \
      > /tmp/python3-purge-simulation.txt \
    && awk ' \
        $1 == "Purg" { print $2 > "/tmp/python3-purge-removed.txt"; next } \
        $1 ~ /^[A-Z][a-z][a-z][a-z]$/ { bad = 1 } \
        END { exit bad + 0 } \
    ' /tmp/python3-purge-simulation.txt \
    && printf 'libpython3-stdlib\nlibpython3.12-minimal\nlibpython3.12-stdlib\npython3\npython3-minimal\npython3.12\npython3.12-minimal\n' > /tmp/python3-purge-expected-unsorted.txt \
    && LC_ALL=C sort /tmp/python3-purge-expected-unsorted.txt > /tmp/python3-purge-expected.txt \
    && LC_ALL=C sort /tmp/python3-purge-removed.txt > /tmp/python3-purge-actual.txt \
    && cmp /tmp/python3-purge-actual.txt /tmp/python3-purge-expected.txt \
    && cat /tmp/python3-purge-simulation.txt \
    && rm /tmp/python3-purge-simulation.txt /tmp/python3-purge-removed.txt /tmp/python3-purge-expected-unsorted.txt /tmp/python3-purge-actual.txt /tmp/python3-purge-expected.txt
RUN test "$TARGETARCH" = amd64 \
    && test "$(dpkg-query -W -f='${Version}' python3)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' python3-minimal)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' libpython3-stdlib)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' python3.12)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' python3.12-minimal)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' libpython3.12-stdlib)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' libpython3.12-minimal)" = 3.12.3-1ubuntu0.15
RUN test "$TARGETARCH" = amd64 \
    && DEBIAN_FRONTEND=noninteractive apt-get purge -y \
      python3 python3-minimal libpython3-stdlib \
      python3.12 python3.12-minimal libpython3.12-stdlib libpython3.12-minimal
RUN set -e; \
    test "$TARGETARCH" = amd64; \
    LC_ALL=C dpkg-query -W -f='${Package} ${db:Status-Status}\n' > /tmp/python3-known.txt; \
    awk '$1 ~ /^(python3|libpython3)/ && $2 != "not-installed" {bad=1} END{exit bad+0}' /tmp/python3-known.txt; \
    find /usr /opt \( -name 'python3*' -o -name 'libpython3*' \) -print > /tmp/python3-leftover.txt; \
    test "$(wc -l < /tmp/python3-leftover.txt)" -eq 0; \
    rm /tmp/python3-known.txt /tmp/python3-leftover.txt
RUN corepack enable && corepack prepare pnpm@11.22.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json tsconfig.json ./
COPY packages ./packages
COPY services/browser-worker ./services/browser-worker
RUN test "$TARGETARCH" = amd64 \
    && curl --fail --location --retry 3 \
      --output /tmp/chrome-for-testing.zip \
      https://storage.googleapis.com/chrome-for-testing-public/157.0.8103.78/linux64/chrome-linux64.zip \
    && echo '9223832977a13db3646201b1341c1f9cf08afa3ceae92540116d7b0c062364fb  /tmp/chrome-for-testing.zip' \
      | sha256sum --check --strict \
    && node services/browser-worker/extract-zip.mjs \
      /tmp/chrome-for-testing.zip /chrome-for-testing \
    && test "$(/chrome-for-testing/chrome-linux64/chrome --version)" \
      = 'Google Chrome for Testing 157.0.8103.78 ' \
    && rm /tmp/chrome-for-testing.zip \
    && pnpm install --frozen-lockfile --filter @slaif-agent-site/browser-worker... \
    && pnpm --filter @slaif-agent-site/browser-tool-contracts build \
    && pnpm --filter @slaif-agent-site/browser-worker build \
    && pnpm --filter @slaif-agent-site/browser-worker deploy --prod --legacy /output \
    && rm -rf /output/node_modules/.bin /output/node_modules/.pnpm/node_modules \
    && rm -f /output/node_modules/.modules.yaml \
      /output/node_modules/.package-map.json /output/node_modules/.pnpm/lock.yaml

# The builder replaces the base browser payload with SHA-256-verified
# Chrome for Testing 157.0.8103.78 (CfT revision 1717349). Compatible
# Chromium libraries come from the exact Playwright Noble base; the base
# image's vulnerable libbrotli1 1.1.0-2build2 is replaced by the fixed
# 1.1.0-2ubuntu0.1 installed from the Noble repositories, and its
# NodeSource nodejs 24.18.1 is purged and replaced with the hash-pinned
# official Node.js 24.22.1 archive (CVE-2026-111497 fixed release).
# No install or download runs after build.
FROM mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e AS runtime
ARG SOURCE_DATE_EPOCH=1704067200
ARG TARGETARCH
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
    BROWSER_WORKER_CHROMIUM_EXECUTABLE=/ms-playwright/chromium-1717349/chrome-linux64/chrome \
    BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=157.0.8103.78 \
    HOME=/tmp \
    NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
WORKDIR /opt/slaif
RUN test "$TARGETARCH" = amd64 \
    && DEBIAN_FRONTEND=noninteractive apt-get purge -y nodejs -o Acquire::Retries=0
# 083-9-c: same fail-closed operation-row simulation, pre-check, exact
# purge and known-record/path absence verification.
RUN test "$TARGETARCH" = amd64 \
    && set -e \
    && LC_ALL=C DEBIAN_FRONTEND=noninteractive apt-get -s purge -y \
      python3 python3-minimal libpython3-stdlib \
      python3.12 python3.12-minimal libpython3.12-stdlib libpython3.12-minimal \
      > /tmp/python3-purge-simulation.txt \
    && awk ' \
        $1 == "Purg" { print $2 > "/tmp/python3-purge-removed.txt"; next } \
        $1 ~ /^[A-Z][a-z][a-z][a-z]$/ { bad = 1 } \
        END { exit bad + 0 } \
    ' /tmp/python3-purge-simulation.txt \
    && printf 'libpython3-stdlib\nlibpython3.12-minimal\nlibpython3.12-stdlib\npython3\npython3-minimal\npython3.12\npython3.12-minimal\n' > /tmp/python3-purge-expected-unsorted.txt \
    && LC_ALL=C sort /tmp/python3-purge-expected-unsorted.txt > /tmp/python3-purge-expected.txt \
    && LC_ALL=C sort /tmp/python3-purge-removed.txt > /tmp/python3-purge-actual.txt \
    && cmp /tmp/python3-purge-actual.txt /tmp/python3-purge-expected.txt \
    && cat /tmp/python3-purge-simulation.txt \
    && rm /tmp/python3-purge-simulation.txt /tmp/python3-purge-removed.txt /tmp/python3-purge-expected-unsorted.txt /tmp/python3-purge-actual.txt /tmp/python3-purge-expected.txt
RUN test "$TARGETARCH" = amd64 \
    && test "$(dpkg-query -W -f='${Version}' python3)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' python3-minimal)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' libpython3-stdlib)" = 3.12.3-0ubuntu2.1 \
    && test "$(dpkg-query -W -f='${Version}' python3.12)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' python3.12-minimal)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' libpython3.12-stdlib)" = 3.12.3-1ubuntu0.15 \
    && test "$(dpkg-query -W -f='${Version}' libpython3.12-minimal)" = 3.12.3-1ubuntu0.15
RUN test "$TARGETARCH" = amd64 \
    && DEBIAN_FRONTEND=noninteractive apt-get purge -y \
      python3 python3-minimal libpython3-stdlib \
      python3.12 python3.12-minimal libpython3.12-stdlib libpython3.12-minimal -o Acquire::Retries=0
RUN set -e; \
    test "$TARGETARCH" = amd64; \
    LC_ALL=C dpkg-query -W -f='${Package} ${db:Status-Status}\n' > /tmp/python3-known.txt; \
    awk '$1 ~ /^(python3|libpython3)/ && $2 != "not-installed" {bad=1} END{exit bad+0}' /tmp/python3-known.txt; \
    find /usr /opt \( -name 'python3*' -o -name 'libpython3*' \) -print > /tmp/python3-leftover.txt; \
    test "$(wc -l < /tmp/python3-leftover.txt)" -eq 0; \
    rm /tmp/python3-known.txt /tmp/python3-leftover.txt
RUN test "$TARGETARCH" = amd64 \
    && apt-get -o Acquire::Retries=0 update \
    && apt-get -o Acquire::Retries=0 install --no-install-recommends --yes \
      'apt=2.8.4ubuntu0.1' \
      'libapt-pkg6.0t64=2.8.4ubuntu0.1' \
    && test "$(dpkg-query -W -f='${Version}' apt)" = 2.8.4ubuntu0.1 \
    && test "$(dpkg-query -W -f='${Version}' libapt-pkg6.0t64)" = 2.8.4ubuntu0.1 \
    && apt-get -o Acquire::Retries=0 install --no-install-recommends --yes 'libbrotli1=1.1.0-2ubuntu0.1' \
    && test "$(dpkg-query -W -f='${Version}' libbrotli1)" = 1.1.0-2ubuntu0.1 \
    && rm -rf /var/lib/apt/lists/*
RUN test "$TARGETARCH" = amd64 \
    && curl --fail --location --retry 3 \
      --output /tmp/node-v24.22.1-linux-x64.tar.gz \
      https://nodejs.org/dist/v24.22.1/node-v24.22.1-linux-x64.tar.gz \
    && echo 'eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c  /tmp/node-v24.22.1-linux-x64.tar.gz' \
      | sha256sum --check --strict \
    && tar -xzf /tmp/node-v24.22.1-linux-x64.tar.gz -C /usr/local --strip-components=1 \
    && rm /tmp/node-v24.22.1-linux-x64.tar.gz \
    && test "$(node --version)" = v24.22.1
RUN rm -rf /ms-playwright /usr/lib/node_modules/npm /usr/lib/node_modules/corepack /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    && rm -f /usr/bin/npm /usr/bin/npx /usr/bin/corepack /usr/bin/pnpm /usr/bin/pnpx \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /usr/local/bin/pnpm /usr/local/bin/pnpx \
    && groupadd --gid 10001 slaif \
    && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent \
      --shell /usr/sbin/nologin slaif
COPY --from=builder --chown=10001:10001 /chrome-for-testing/chrome-linux64 /ms-playwright/chromium-1717349/chrome-linux64
COPY --from=builder --chown=10001:10001 /output ./
USER 10001:10001
EXPOSE 3100
CMD ["node", "dist/server.js"]

# NGINX Open Source 1.30.6; two-clause BSD license; official multi-platform
# image (Alpine 3.24). The overlay pins the exact OpenSSL fix versions and
# the brotli-libs security fix from the base image's own v3.24 repositories.
FROM nginx:1.30.6-alpine3.24@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site NGINX edge" \
      org.opencontainers.image.description="NGINX Open Source edge for the SLAIF Agent-Site deployment skeleton" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
RUN apk --timeout 30 add --no-cache \
      'brotli-libs=1.2.1-r0' \
      'libcrypto3=3.5.9-r0' \
      'libssl3=3.5.9-r0' \
    && test "$(awk '/^P:brotli-libs$/{found=1} found && /^V:/{print substr($0,3); exit}' /lib/apk/db/installed)" = "1.2.1-r0" \
    && test "$(awk '/^P:libcrypto3$/{found=1} found && /^V:/{print substr($0,3); exit}' /lib/apk/db/installed)" = "3.5.9-r0" \
    && test "$(awk '/^P:libssl3$/{found=1} found && /^V:/{print substr($0,3); exit}' /lib/apk/db/installed)" = "3.5.9-r0" \
    && apk del curl
COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]

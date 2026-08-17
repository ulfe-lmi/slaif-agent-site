# NGINX Open Source 1.29.7; two-clause BSD license; official multi-platform image.
FROM nginx:1.29.7-alpine3.23@sha256:e7257f1ef28ba17cf7c248cb8ccf6f0c6e0228ab9c315c152f9c203cd34cf6d1
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
      'libcrypto3=3.5.7-r0' \
      'libssl3=3.5.7-r0' \
    && apk del curl
COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]

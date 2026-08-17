# Apache HTTP Server 2.4.68; Apache-2.0 license; official multi-platform image.
FROM httpd:2.4.68-alpine3.23@sha256:4a15e9c73f25334bc03cfb3c692c9adfc103bb46ca89cee1f0b9a5fcbc7b21f6
ARG SOURCE_DATE_EPOCH=1704067200
ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z
ARG SLAIF_IMAGE_REVISION=local
ARG SLAIF_IMAGE_VERSION=0.0.0
LABEL org.opencontainers.image.title="SLAIF Agent-Site Apache edge" \
      org.opencontainers.image.description="Apache HTTP Server reference edge for the SLAIF Agent-Site deployment skeleton" \
      org.opencontainers.image.source="https://github.com/ulfe-lmi/slaif-agent-site" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="${SLAIF_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${SLAIF_IMAGE_REVISION}" \
      org.opencontainers.image.created="${SLAIF_IMAGE_CREATED}"
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}
RUN apk --timeout 30 add --no-cache \
      'apr-util=1.6.4-r0' \
      'apr-util-ldap=1.6.4-r0' \
      'libcrypto3=3.5.7-r0' \
      'libssl3=3.5.7-r0' \
    && apk del perl \
    && sed -i \
      -e 's/^#LoadModule headers_module/LoadModule headers_module/' \
      -e 's/^#LoadModule proxy_module/LoadModule proxy_module/' \
      -e 's/^#LoadModule proxy_http_module/LoadModule proxy_http_module/' \
      -e 's/^#LoadModule unique_id_module/LoadModule unique_id_module/' \
      -e 's/^#LoadModule deflate_module/LoadModule deflate_module/' \
      /usr/local/apache2/conf/httpd.conf \
    && printf '\nInclude conf/extra/slaif-agent-site.conf\n' >> /usr/local/apache2/conf/httpd.conf
COPY infra/apache/slaif-agent-site.conf /usr/local/apache2/conf/extra/slaif-agent-site.conf
RUN httpd -t

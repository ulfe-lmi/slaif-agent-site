# Apache HTTP Server 2.4.68 on Debian Trixie; Apache-2.0 license; official image.
FROM httpd:2.4.68-trixie@sha256:979c38c2228d28c2edfd45c6e27dcee1c7b4a101a5526721ae8ece454e89e99e
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
RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
      'libaprutil1-ldap=1.6.3-3+deb13u1' \
      'libaprutil1t64=1.6.3-3+deb13u1' \
      'libssl3t64=3.5.7-1~deb13u2' \
      'openssl=3.5.7-1~deb13u2' \
    && apt-get purge --allow-remove-essential --yes \
      libcurl4t64 libxml2 perl-base \
    && rm -rf /var/lib/apt/lists/* \
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

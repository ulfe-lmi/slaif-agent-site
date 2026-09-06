# Apache HTTP Server 2.4 on Ubuntu 24.04 LTS; Apache-2.0 license; official image.
FROM ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517
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
      'apache2=2.4.58-1ubuntu8.15' \
      'apache2-bin=2.4.58-1ubuntu8.15' \
      'apache2-data=2.4.58-1ubuntu8.15' \
      'apache2-utils=2.4.58-1ubuntu8.15' \
      'openssl=3.0.13-0ubuntu3.15' \
    && a2dissite 000-default \
    && a2enmod deflate headers proxy proxy_http unique_id \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*
COPY infra/apache/slaif-agent-site.conf /etc/apache2/sites-available/slaif-agent-site.conf
RUN a2ensite slaif-agent-site && apachectl -t
CMD ["apachectl", "-D", "FOREGROUND"]

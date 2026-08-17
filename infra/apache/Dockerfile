# Apache HTTP Server 2.4.66; Apache-2.0 license; official multi-platform image.
FROM httpd:2.4.66-alpine3.23@sha256:968c8b4098fcecb473762b45f6c541a3b2b2cfab2caccb1edbd2cece071ef160
RUN sed -i \
      -e 's/^#LoadModule headers_module/LoadModule headers_module/' \
      -e 's/^#LoadModule proxy_module/LoadModule proxy_module/' \
      -e 's/^#LoadModule proxy_http_module/LoadModule proxy_http_module/' \
      -e 's/^#LoadModule unique_id_module/LoadModule unique_id_module/' \
      -e 's/^#LoadModule deflate_module/LoadModule deflate_module/' \
      /usr/local/apache2/conf/httpd.conf \
    && printf '\nInclude conf/extra/slaif-agent-site.conf\n' >> /usr/local/apache2/conf/httpd.conf
COPY infra/apache/slaif-agent-site.conf /usr/local/apache2/conf/extra/slaif-agent-site.conf
RUN httpd -t

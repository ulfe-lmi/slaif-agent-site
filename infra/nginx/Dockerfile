# NGINX Open Source 1.29.6; two-clause BSD license; official multi-platform image.
FROM nginx:1.29.6-alpine3.23@sha256:f46cb72c7df02710e693e863a983ac42f6a9579058a59a35f1ae36c9958e4ce0
COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]

# Construit depuis le contexte "apps/" :
#   docker build -f hub/Dockerfile -t lyux-hub .
FROM nginx:1.27-alpine

LABEL org.opencontainers.image.title="LyuX Hub" \
      org.opencontainers.image.description="Interface d'administration LyuX (plugins Cockpit servis de maniere autonome)"

COPY hub/nginx.conf /etc/nginx/conf.d/default.conf
COPY hub/www/ /usr/share/nginx/html/
COPY hub/base1/ /usr/share/nginx/html/base1/

COPY cockpit/lyux/ /usr/share/nginx/html/lyux/
COPY cockpit/parc/ /usr/share/nginx/html/parc/
COPY cockpit/discover/ /usr/share/nginx/html/discover/
COPY cockpit/users/ /usr/share/nginx/html/users/

EXPOSE 80

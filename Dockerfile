FROM nginx:alpine
LABEL org.opencontainers.image.source="https://github.com/igedesurya/signal-bot"
LABEL org.opencontainers.image.description="Signal Bot - dashboard sinyal tren kripto (read-only)"

# dashboard jadi halaman utama
COPY dashboard.html /usr/share/nginx/html/index.html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1

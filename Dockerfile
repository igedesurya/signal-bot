FROM python:3.12-alpine
LABEL org.opencontainers.image.source="https://github.com/igedesurya/signal-bot"
LABEL org.opencontainers.image.description="Signal Bot - dashboard sinyal tren + proxy Yahoo (read-only)"

WORKDIR /app
COPY dashboard.html index.html
COPY dashboard.html dashboard.html
COPY server.py server.py

ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/api/health >/dev/null 2>&1 || exit 1
CMD ["python", "server.py"]

# Stage 1: build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: backend + static
FROM python:3.14-slim
LABEL org.opencontainers.image.source="https://github.com/xiaomonk88/message_info" \
      org.opencontainers.image.description="万能信息管理系统 — 动态字段 / 板块化管理 / Docker 一键部署" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    DATABASE_URL=sqlite:////data/db/app.db \
    UPLOAD_DIR=/data/uploads \
    BACKUP_DIR=/data/backups \
    STATIC_DIR=/app/static

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tzdata && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-builder /app/dist ./static

RUN mkdir -p /data/db /data/uploads /data/backups /data/secrets
VOLUME ["/data"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/system/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

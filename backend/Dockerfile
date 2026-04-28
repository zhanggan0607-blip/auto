FROM python:3.11-slim AS builder

ARG VERSION=v1.0.0

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null; \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-production.txt ./requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --prefix=/install -r requirements.txt

FROM python:3.11-slim

ARG VERSION=v1.0.0
ARG DOCKER_GID=988

LABEL maintainer="Bid Auto System"
LABEL version="${VERSION}"
LABEL description="天齐AI投标平台 - 后端服务"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null; \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser && \
    groupadd -g ${DOCKER_GID} docker 2>/dev/null || true && \
    usermod -aG docker appuser 2>/dev/null || true && \
    mkdir -p /var/log/bid_auto && \
    mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    chown -R appuser:appuser /var/log/bid_auto /app/staticfiles /app/media /app

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "120"]

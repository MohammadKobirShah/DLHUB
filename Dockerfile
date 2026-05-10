"""
DLHUB - Multi-stage Production Dockerfile
==========================================
Optimized for size and security.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir yt-dlp

RUN useradd -m -u 1000 -s /bin/bash appuser || true

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser . /app

RUN mkdir -p /downloads /logs /tmp/dlhub && \
    chown -R appuser:appuser /downloads /logs /tmp/dlhub

USER appuser

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONMALLOC=debug

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

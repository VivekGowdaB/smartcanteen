# ==========================================
# Multi-stage Dockerfile for Smart Canteen
# Stage 1: Build & Dependencies
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into virtualenv wheel cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================
# Stage 2: Minimal Production Runtime
# ==========================================
FROM python:3.12-slim AS runtime

LABEL maintainer="DevOps Team (ABL 1) <devops@college.edu>"
LABEL description="Smart Canteen Ordering System Micro-project"
LABEL version="1.0"

WORKDIR /app

# Create non-root system group and user (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=appuser:appgroup . /app

# Ensure correct permissions for data and logs
RUN mkdir -p /app/instance /app/reports && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment configurations
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=5000

EXPOSE 5000

# Container Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://localhost:5000/health').getcode() == 200 else 1; import sys; sys.exit(sys_exit)"

# Production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]

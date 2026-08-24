# ── STAGE 1: Builder (compilação de wheels C/Postgres) ──────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ── STAGE 2: Runtime (imagem final enxuta) ──────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/* && rm -rf /wheels

COPY . .

RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/login/ || exit 1

CMD ["sh", "-c", \
    "python manage.py collectstatic --noinput && \
     python manage.py migrate && \
     python manage.py setup_inicial && \
     gunicorn setup.wsgi:application \
       --bind 0.0.0.0:${PORT:-8000} \
       --workers 2 \
       --timeout 120"]

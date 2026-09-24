# Multi-stage build. The builder compiles wheels; the runtime image carries
# only the installed packages and the app, so it stays small and holds no
# build toolchain.

# ---------- builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# Dependencies are copied on their own so this layer is cached and only
# reinstalls when requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------- runtime ----------
FROM python:3.11-slim AS runtime

# PYTHONDONTWRITEBYTECODE: no .pyc clutter in the image.
# PYTHONUNBUFFERED: logs reach docker logs immediately rather than sitting
# in a buffer, which matters when debugging a container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"

# curl is needed by the compose healthcheck below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user. If the container is ever compromised, the blast
# radius is a user that owns nothing.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser static/ ./static/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.13-slim

# System deps:
#   ffmpeg          — required by scenedetect + pixeltable video_splitter
#   libgl1 libglib  — required by opencv-python-headless on slim Debian
#   ca-certificates — outbound HTTPS to Twelve Labs
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      libgl1 \
      libglib2.0-0 \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer — cached unless pyproject/uv.lock change
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Backend code
COPY backend/ .

# scripts/ lives at the repo root; download_videos.py expects it at ../scripts/
COPY scripts/ /scripts/

# Pixeltable data lives on a mounted disk in production.
ENV PIXELTABLE_HOME=/var/pixeltable

EXPOSE 8000

# Render disk mounts can have permissions that Postgres rejects (needs 0700).
# Fix pgdata permissions on every boot so redeployed containers don't crash.
COPY <<'EOF' /app/entrypoint.sh
#!/bin/sh
set -e
PGDATA="${PIXELTABLE_HOME:-/var/pixeltable}/pgdata"
if [ -d "$PGDATA" ]; then
  chmod 700 "$PGDATA"
  rm -f "$PGDATA/postmaster.pid"
fi
exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
EOF
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

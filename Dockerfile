FROM python:3.13-slim

# System deps:
#   ffmpeg          — required by scenedetect + pixeltable video_splitter
#   libgl1 libglib  — required by opencv-python-headless on slim Debian
#   ca-certificates — outbound HTTPS to Twelve Labs
#   curl            — download_videos.py --r2 pulls video files from the R2 mirror
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      libgl1 \
      libglib2.0-0 \
      ca-certificates \
      curl \
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
  # A previous container leaves its Unix-socket lock on the persistent disk.
  # On the next deploy a fresh postmaster sees that stale lock and refuses to
  # start ("FATAL: lock file .s.PGSQL.5432.lock already exists"), taking the
  # whole DB — and every DB-backed endpoint — down with a 500. At container
  # boot no postmaster is running yet, so any such lock is stale; clear it.
  # Guard: keep it only if its recorded PID is a *live postgres* process
  # (defends against a coincidental PID reuse in the new namespace).
  LOCK="$PGDATA/.s.PGSQL.5432.lock"
  if [ -f "$LOCK" ]; then
    LOCKPID=$(head -n1 "$LOCK" 2>/dev/null || true)
    KEEP=0
    if [ -n "$LOCKPID" ] && kill -0 "$LOCKPID" 2>/dev/null; then
      if grep -qa postgres "/proc/$LOCKPID/cmdline" 2>/dev/null; then
        KEEP=1
      fi
    fi
    if [ "$KEEP" -eq 0 ]; then
      echo "entrypoint: clearing stale Postgres socket lock (pid '$LOCKPID')"
      rm -f "$LOCK" "$PGDATA/.s.PGSQL.5432"
    fi
  fi
fi
exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
EOF
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

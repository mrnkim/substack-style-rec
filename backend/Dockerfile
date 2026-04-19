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
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# App code
COPY . .

# Pixeltable data lives on a mounted disk in production.
# Override in the host (Render Disk / Fly Volume / docker run -v ...).
ENV PIXELTABLE_HOME=/var/pixeltable

EXPOSE 8000

# PORT is injected by Render. Fall back to 8000 for local `docker run`.
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]

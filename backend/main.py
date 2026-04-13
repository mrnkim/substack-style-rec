import config  # load .env before any other imports that read env vars
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import pixeltable as pxt
from routers import videos, creators, recommendations, search

VIDEO_FILES_DIR = Path(__file__).resolve().parent / "video_files"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Only show our app logs + errors from third-party
for name in ("httpx", "httpcore", "pixeltable_pgserver", "uvicorn.access"):
    logging.getLogger(name).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        pxt.get_table(f"{config.APP_NAMESPACE}.videos")
        logger.info("Connected to Pixeltable schema")
    except Exception:
        logger.warning(
            "Pixeltable schema not initialized. "
            "Run 'uv run setup_pixeltable.py' first. "
            "The server will start but API calls will fail."
        )
    yield


app = FastAPI(
    title="Substack Rec Backend",
    description="Pixeltable-powered video recommendations for Substack TV demo",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(creators.router)
app.include_router(recommendations.router)
app.include_router(search.router)

VIDEO_FILES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/files", StaticFiles(directory=str(VIDEO_FILES_DIR)), name="uploaded-files")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["data/*", "*.log"],
        log_level="warning",
    )

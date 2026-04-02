import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import pixeltable as pxt

import config
from routers import videos, creators, recommendations, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        pxt.get_table(f"{config.APP_NAMESPACE}.videos")
        logger.info("Connected to PixelTable schema")
    except Exception:
        logger.warning(
            "PixelTable schema not initialized. "
            "Run 'python setup_pixeltable.py' then 'python ingest.py' first. "
            "The server will start but API calls will fail."
        )
    yield


app = FastAPI(
    title="Substack Rec Backend",
    description="PixelTable-powered video recommendations for Substack TV demo",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["data/*", "*.log"],
    )

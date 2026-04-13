"""Video listing and detail endpoints.

Also exports shared helpers used by other routers:
    VIDEO_FIELDS, _select_videos, _attach_attrs, _build_video_response,
    _load_creators_map, _get_scenes_table, _scene_similarity, _title_similarity
"""

import logging
import subprocess
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
import pixeltable as pxt

import config
from models import (
    CreatorResponse,
    PaginatedVideosResponse,
    UploadVideoResponse,
    VideoAttributesResponse,
    VideoResponse,
)

VIDEO_FILES_DIR = Path(__file__).resolve().parent.parent / "video_files"
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["videos"])

VIDEO_FIELDS = (
    "id",
    "title",
    "creator_id",
    "category",
    "duration",
    "thumbnail_url",
    "hls_url",
    "upload_date",
)


def _get_scenes_table():
    """Return the video_scenes view, or None if unavailable."""
    try:
        return pxt.get_table(f"{config.APP_NAMESPACE}.video_scenes")
    except Exception:
        return None


ATTR_FIELDS = ("topic", "style", "tone")
ALL_FIELDS = VIDEO_FIELDS + ATTR_FIELDS


def _select_videos(videos_t, query=None, include_attrs: bool = True):
    """Select video fields, including computed attrs when available."""
    q = query if query is not None else videos_t
    if include_attrs:
        try:
            cols = [getattr(videos_t, f) for f in ALL_FIELDS]
            return q.select(*cols)
        except Exception:
            pass
    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    return q.select(*cols)


def _scene_similarity(
    scenes_t,
    exclude_ids: set[str] | None = None,
    limit: int = 10,
    creator_id: str | None = None,
    **sim_kwargs,
) -> list[dict]:
    """Query video_segment embeddings on scenes view, deduplicate to unique videos.

    Accepts any similarity kwargs: string="text", image="/path", video="/path", audio="/path".
    """
    sim = scenes_t.video_segment.similarity(**sim_kwargs)
    query = scenes_t
    if creator_id:
        query = query.where(scenes_t.creator_id == creator_id)

    exclude = exclude_ids or set()
    cols = [getattr(scenes_t, f) for f in VIDEO_FIELDS]
    scene_rows = list(
        query.order_by(sim, asc=False)
        .limit((limit + len(exclude)) * 5)
        .select(*cols, score=sim)
        .collect()
    )

    seen: set[str] = set()
    deduped: list[dict] = []
    for row in scene_rows:
        vid = row["id"]
        if vid not in seen and vid not in exclude:
            seen.add(vid)
            deduped.append(row)
            if len(deduped) >= limit:
                break
    return deduped


def _title_similarity(
    videos_t,
    query_string: str,
    exclude_ids: set[str] | None = None,
    limit: int = 10,
    creator_id: str | None = None,
) -> list[dict]:
    """Title-embedding similarity on the videos table (fallback)."""
    sim = videos_t.title.similarity(string=query_string)
    query = videos_t
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    exclude = exclude_ids or set()
    cols = [getattr(videos_t, f) for f in VIDEO_FIELDS]
    rows = list(
        query.order_by(sim, asc=False)
        .limit(limit + len(exclude))
        .select(*cols, score=sim)
        .collect()
    )
    return [r for r in rows if r["id"] not in exclude]


def _attach_attrs(rows: list[dict], videos_t) -> None:
    """Attach topic/style/tone to rows missing them (e.g. from chunk queries)."""
    if not rows or rows[0].get("topic") is not None:
        return
    try:
        row_ids = [r["id"] for r in rows]
        attr_rows = list(
            videos_t.where(videos_t.id.isin(row_ids))
            .select(videos_t.id, videos_t.topic, videos_t.style, videos_t.tone)
            .collect()
        )
        attr_map = {r["id"]: r for r in attr_rows}
        for row in rows:
            attrs = attr_map.get(row["id"], {})
            row["topic"] = attrs.get("topic")
            row["style"] = attrs.get("style")
            row["tone"] = attrs.get("tone")
    except Exception as e:
        logger.debug("Could not load attributes: %s", e)


def _build_video_response(row: dict, creators_map: dict[str, dict]) -> VideoResponse:
    """Convert a Pixeltable row dict into a VideoResponse with nested creator."""
    cid = row.get("creator_id", "")
    cdata = creators_map.get(cid, {})

    attributes = None
    if row.get("topic") or row.get("style") or row.get("tone"):
        attributes = VideoAttributesResponse(
            topic=row["topic"] if isinstance(row.get("topic"), list) else [],
            style=row.get("style") or "",
            tone=row.get("tone") or "",
        )

    return VideoResponse(
        id=row["id"],
        title=row.get("title", ""),
        creator=CreatorResponse(
            id=cid,
            name=cdata.get("name", ""),
            avatar_url=cdata.get("avatar_url", ""),
            description=cdata.get("description", ""),
            video_count=cdata.get("video_count", 0),
        ),
        category=row.get("category", "interview"),
        duration=row.get("duration", 0),
        thumbnail_url=row.get("thumbnail_url", ""),
        hls_url=row.get("hls_url"),
        upload_date=row.get("upload_date", ""),
        attributes=attributes,
    )


_creators_cache: dict[str, dict] | None = None
_creators_cache_ts: float = 0.0
_CREATORS_CACHE_TTL = 300.0  # 5 minutes


def _load_creators_map() -> dict[str, dict]:
    """Load all creators keyed by id, with video_count. Cached for 5 min."""
    global _creators_cache, _creators_cache_ts
    now = time.monotonic()
    if _creators_cache is not None and (now - _creators_cache_ts) < _CREATORS_CACHE_TTL:
        return _creators_cache

    creators_t = pxt.get_table(f"{config.APP_NAMESPACE}.creators")
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")

    creators = {
        c["id"]: {
            "name": c["name"],
            "avatar_url": c["avatar_url"],
            "description": c["description"],
            "video_count": 0,
        }
        for c in creators_t.select(
            creators_t.id,
            creators_t.name,
            creators_t.avatar_url,
            creators_t.description,
        ).collect()
    }
    for r in videos_t.select(videos_t.creator_id).collect():
        cid = r.get("creator_id", "")
        if cid in creators:
            creators[cid]["video_count"] += 1

    _creators_cache = creators
    _creators_cache_ts = now
    return creators


@router.get("/videos", response_model=PaginatedVideosResponse)
def list_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    creator_id: str | None = None,
):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    creators_map = _load_creators_map()

    query = videos_t
    if category:
        query = query.where(videos_t.category == category)
    if creator_id:
        query = query.where(videos_t.creator_id == creator_id)

    all_rows = list(_select_videos(videos_t, query).collect())
    total = len(all_rows)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    rows = all_rows[start : start + limit]
    _attach_attrs(rows, videos_t)

    return PaginatedVideosResponse(
        data=[_build_video_response(r, creators_map) for r in rows],
        page=page,
        total=total,
        total_pages=total_pages,
    )


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: str):
    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    rows = list(
        _select_videos(videos_t, videos_t.where(videos_t.id == video_id)).collect()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Video not found")

    _attach_attrs(rows, videos_t)
    return _build_video_response(rows[0], _load_creators_map())


# ── Self-serve video upload ─────────────────────────────────────────────────


@router.post("/videos/upload", response_model=UploadVideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("interview"),
):
    """Upload a video file. Pixeltable auto-runs scene detection, embedding,
    and attribute extraction. File size limited by MAX_UPLOAD_SIZE_MB."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_VIDEO_TYPES:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in {".mp4", ".webm", ".mov"}:
            raise HTTPException(status_code=400, detail="Only mp4/webm/mov files accepted")

    max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    VIDEO_FILES_DIR.mkdir(parents=True, exist_ok=True)
    video_id = f"upload_{uuid.uuid4().hex[:12]}"
    dest = VIDEO_FILES_DIR / f"{video_id}.mp4"

    size = 0
    with dest.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Max {config.MAX_UPLOAD_SIZE_MB}MB.",
                )
            f.write(chunk)

    logger.info("upload: %s (%s, %.1f MB)", title[:40], video_id, size / 1e6)

    duration = _probe_duration(dest)
    thumb_path = _extract_thumbnail(dest, video_id)
    thumb_url = f"/api/files/{video_id}_thumb.jpg" if thumb_path else ""
    video_url = f"/api/files/{video_id}.mp4"

    from datetime import date

    videos_t = pxt.get_table(f"{config.APP_NAMESPACE}.videos")
    videos_t.insert(
        [{
            "id": video_id,
            "title": title,
            "creator_id": "user_upload",
            "category": category,
            "duration": duration,
            "thumbnail_url": thumb_url,
            "hls_url": video_url,
            "upload_date": date.today().isoformat(),
            "video": str(dest),
        }],
        on_error="ignore",
    )

    global _creators_cache
    _creators_cache = None

    return UploadVideoResponse(id=video_id, title=title, status="processing")


def _probe_duration(path: Path) -> int:
    """Get video duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return round(float(result.stdout.strip()))
    except Exception:
        return 0


def _extract_thumbnail(video_path: Path, video_id: str) -> Path | None:
    """Extract a thumbnail frame at 2 seconds into the video."""
    thumb_path = VIDEO_FILES_DIR / f"{video_id}_thumb.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "2", "-i", str(video_path),
             "-vframes", "1", "-q:v", "3", str(thumb_path)],
            capture_output=True, timeout=15,
        )
        if thumb_path.exists() and thumb_path.stat().st_size > 0:
            return thumb_path
    except Exception:
        pass
    return None

# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-04-28
>
> This file is a short, current snapshot. Canonical docs:
> - **Setup & quick start** → [`README.md`](./README.md)
> - **Backend API spec** → [`docs/BACKEND_SPEC.md`](./docs/BACKEND_SPEC.md)
> - **Agent guide** → [`CLAUDE.md`](./CLAUDE.md)

## Project Overview

AI-powered video recommendation demo in the style of Substack TV. Uses Twelve Labs Marengo 3.0 embeddings + Pixeltable for semantic, explainable, cross-creator recommendations.

**Goal**: Demonstrate TwelveLabs multimodal video understanding for ISV creator platforms (Substack, UScreen, Kajabi) with Netflix-style discovery.

## Architecture

```
Next.js 16 frontend (Vercel: substack-style-rec.vercel.app)
       |  NEXT_PUBLIC_API_BASE
       v
FastAPI backend (Render: substack-rec-api-g2ui.onrender.com)
       |
       v
Pixeltable (embedded PostgreSQL on Render persistent disk)
  ├── creators table (10 creators)
  ├── videos table (25 indexed videos + Analyze API attrs)
  └── title_marengo embedding index (text similarity)
       |
       v
Twelve Labs API (Embed v2, Analyze, Search)
       |
Cloudflare R2 (video file storage: tl-substack-style-app bucket)
```

### Data flow

- **Default** — Browser → Next.js `/api/*` routes → Twelve Labs (fallback when no backend).
- **With backend** — Set `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`. Browser → FastAPI → Pixeltable → Twelve Labs.

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, hls.js |
| Backend | FastAPI + Pixeltable + `uv` package management |
| Embeddings | Twelve Labs Marengo 3.0 (512-dim), scene-level + title fallback |
| Attribute Extraction | Twelve Labs Analyze API (topic / style / tone) |
| Scene Search | Twelve Labs Search API (returns scene-level timestamps) |
| Video Player | hls.js with CloudFront HLS URLs from Twelve Labs |
| Video Storage | Cloudflare R2 (`tl-substack-style-app` bucket, public) |
| DB Storage | Embedded Pixeltable Postgres on Render persistent disk (20 GB) |
| Deployment | Vercel (frontend) + Render Starter (backend, $12/mo) |

## Implementation Status

### Complete
- Pixeltable schema: creators + videos tables with title-level Marengo 3.0 embeddings.
- Analyze API computed columns: topic, style, tone run automatically on INSERT.
- All endpoints: `/api/videos`, `/api/creators`, `/api/recommendations/{for-you,similar,creator-catalog}`, `/api/search`.
- 70 / 30 subscription / discovery split with max-2-per-creator diversity.
- Explainable recommendations: short reason + matchedAttributes as individual pills (topic overlap, style/tone, creator context).
- Cold start fallback (latest from subscriptions + discovery).
- Text search via Twelve Labs Search API with scene-level timestamps and scene thumbnails.
- Search results show rank badge, scene time range, category pill, and matched scene thumbnail.
- Nav: Subscriptions dropdown (count + list + unsubscribe) and Watch History dropdown (thumbnails + reset).
- Console logging of recommendation scores for debugging (browser DevTools).
- Video player supports `?t=` query param for scene-level deep linking.
- Resilience: title-similarity fallback on API failures, frontend decoupled loading.
- Production deployment: Vercel (frontend) + Render (backend) + Cloudflare R2 (video files).
- Video download from R2 instead of YouTube (YouTube blocks data center IPs).

### Open / Known Issues
- **video_scenes view not created on Render** — Starter plan (0.5 CPU, 512 MB) cannot run scene_detect_histogram on 25 videos. Text search uses TL Search API as workaround. Recommendations use title_marengo fallback.
- **Render Starter auto-sleep** — 15 min inactivity causes ~30s cold start. Hit `/health` before demos.
- **Multimodal file search disabled** — Image/video/audio upload search removed from UI (requires video_scenes view). Backend code preserved for future re-enablement.
- Session-based live personalization (re-rank within a session based on in-session clicks).
- Scene detection could be re-enabled with Standard plan ($25/mo) or by pre-computing on a local machine and uploading the DB.

## Content

25 longform videos indexed in Twelve Labs, drawn from a curated set of 30 across 11 creators and 4 categories. Full breakdown in [`README.md`](./README.md#content) and the raw list in [`scripts/curate_videos.csv`](./scripts/curate_videos.csv).

- **Twelve Labs index**: `69c37b6708cd679f8afbd748` (`substack-style-rec`)
- **Models**: Marengo 3.0 (visual + audio), Pegasus 1.2
- **user_metadata** schema per video (written by `scripts/update_tl_metadata.py`): `youtubeId`, `creatorId`, `creatorName`, `category`, `uploadDate`.

## Scripts

Data curation (one-time, lives in `scripts/`):

| Script | Purpose |
|---|---|
| `download_and_collect.py` | Download YouTube videos + collect metadata CSVs |
| `update_tl_metadata.py` | Upload creator/category metadata into TL `user_metadata` |
| `curate_videos.csv` | Curated YouTube IDs + category |
| `creators_metadata.csv`, `videos_metadata.csv` | Creator + per-video metadata |
| `CURATION_GUIDE.md` | Channel suggestions + selection criteria |

Runtime (lives in `backend/`, run with `uv`):

| Script | Purpose |
|---|---|
| `download_videos.py` | Fetch video files from Cloudflare R2 for Pixeltable ingestion |
| `setup_pixeltable.py` | Create schema, ingest, build scene view + embedding indexes |
| `run_setup_logged.sh` | Same, with `pxt.drop_dir` reset + logging to `backend/logs/` |
| `main.py` | Start FastAPI on `:8000` |

## Key Decisions

1. **Dual data source** — Frontend works against Next.js `/api/*` (TL direct) or FastAPI + Pixeltable, toggled by `NEXT_PUBLIC_API_BASE`. Keeps the demo runnable without the backend.
2. **TL Search API for text search** — Text search calls Twelve Labs Search API directly (returns scene-level timestamps + thumbnails). Falls back to Pixeltable title_marengo similarity when TL API is unavailable or for creator-filtered queries.
3. **Recommendations via Pixeltable** — For-you / similar / creator-catalog still use Pixeltable title_marengo embeddings for similarity. TL Search API is only used for the search endpoint.
4. **`user_metadata` as source of truth** — Creator / category / upload date live in Twelve Labs, not in local JSON. `scripts/update_tl_metadata.py` writes; runtime only reads.
5. **Analyze as computed columns** — Topic / style / tone run automatically on INSERT, so attribute-based recommendation reasons are always available.
6. **Diversity + hybrid discovery** — 70 / 30 subscription / discovery split with max 2 videos per creator. Prevents the classic filter bubble without abandoning subscribed creators.
7. **Reason + attributes separation** — `generate_reason` returns a short "Because you watched X" string. `_matched_attrs` returns topic/style/tone/creator context as separate pills for visual display.
8. **Video files on R2** — YouTube blocks data center IPs, so videos are hosted on Cloudflare R2 (`tl-substack-style-app` bucket, public URL). `download_videos.py` fetches from R2 instead of YouTube.
9. **Render deployment** — Blueprint-based deploy from `render.yaml`. Persistent disk at `/var/pixeltable` stores embedded Postgres + video files. Entrypoint script fixes pgdata permissions on redeploy.
10. **Resilience by default** — Twelve Labs rate-limits, 502s, and file-size limits all degrade gracefully to title similarity or empty results rather than 500s or hung frontends.

## Deployment

### Production URLs
- **Frontend**: https://substack-style-rec.vercel.app
- **Backend**: https://substack-rec-api-g2ui.onrender.com
- **R2 Videos**: https://pub-3d90ba141b2a453d9ada94f279c78419.r2.dev/

### Render Setup
1. Blueprint from `render.yaml` → creates web service (Starter, $7/mo) + disk (20 GB, $5/mo).
2. Set env vars: `TWELVELABS_API_KEY`, `CORS_ORIGINS`, `TWELVELABS_INDEX_ID`.
3. After deploy, Shell: `uv run download_videos.py --full && uv run setup_pixeltable.py --full`
4. Manual Deploy to restart server with populated DB.
5. If PostgreSQL lock errors after redeploy: `rm -f /var/pixeltable/pgdata/.s.PGSQL.5432.lock /var/pixeltable/pgdata/.s.PGSQL.5432 /var/pixeltable/pgdata/postmaster.pid`

### Cloudflare R2
- Bucket: `tl-substack-style-app` (25 video files, ~3.4 GB)
- Public URL enabled. Files have URL-safe names (special chars removed from originals).
- Upload via `npx wrangler r2 object put --remote` (< 300 MB) or `aws s3 cp --endpoint-url` (> 300 MB).

## Environment Variables

### Frontend (`.env.local` at repo root)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
NEXT_PUBLIC_API_BASE=http://localhost:8000/api   # Optional: use Pixeltable backend
```

### Backend (`backend/.env.local` or `backend/.env` — `config.py` loads both)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
CORS_ORIGINS=http://localhost:3000,http://localhost:3002
PIXELTABLE_HOME=./data                            # Optional: scope Pixeltable to this repo
```

### Render (set in dashboard, not committed)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
CORS_ORIGINS=https://substack-style-rec.vercel.app
PIXELTABLE_HOME=/var/pixeltable
```

See [`README.md`](./README.md#quick-start) for the full run order.

## Recent Changes (2026-04-22 → 2026-04-28)

- **Recommendation explainability**: Separated reason (short text) from matchedAttributes (pills). Topic overlap prioritized, creator context added ("New creator: X", "From your subscriptions").
- **Nav dropdowns**: Subscriptions (count + list + unsubscribe) and Watch History (thumbnails + reset all) added to navigation bar.
- **TL Search API integration**: Text search now calls Twelve Labs Search API directly, returning scene-level start/end timestamps and scene thumbnails. No Pixeltable scene detection needed.
- **Search UI overhaul**: Results show rank badge, scene time range, category pill next to title, and matched scene thumbnail. File upload search removed (not in PRD).
- **Video download from R2**: Replaced yt-dlp with direct R2 downloads. Removed yt-dlp dependency.
- **Render deployment**: Dockerfile moved to repo root, entrypoint fixes pgdata permissions. Blueprint-based deploy with persistent disk.
- **Console logging**: Browser DevTools shows recommendation scores for For You and Similar endpoints.
- **VideoPlayer startTime**: Supports `?t=` query param for scene-level deep linking from search results.

# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-04-18
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
Next.js 16 frontend (localhost:3000)
       |  NEXT_PUBLIC_API_BASE
       v
FastAPI backend (localhost:8000)
       |
       v
Pixeltable
  ├── creators table (11 creators)
  ├── videos table (25 indexed videos + pxt.Video + Analyze API attrs)
  ├── video_scenes view (scene_detect_histogram + video_splitter mode=fast)
  ├── scene_marengo embedding index (per-scene Marengo 3.0 vectors)
  └── title_marengo embedding index (text fallback)
       |
       v
Twelve Labs API (Embed v2 + Analyze)
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
| Scene Detection | Pixeltable `scene_detect_histogram` + `video_splitter(mode='fast')` |
| Video Player | hls.js with CloudFront HLS URLs from Twelve Labs |
| Storage | Local Pixeltable Postgres (`PIXELTABLE_HOME`) |

## Implementation Status

### Complete
- Pixeltable schema: creators + videos + `video_scenes` view with scene-level Marengo 3.0 embeddings.
- Scene detection via `scene_detect_histogram` + stream-copy `video_splitter(mode='fast')` — no re-encoding.
- Analyze API computed columns: topic, style, tone run automatically on INSERT.
- All endpoints: `/api/videos`, `/api/creators`, `/api/recommendations/{for-you,similar,creator-catalog}`, `/api/search` (GET text + POST multimodal).
- 70 / 30 subscription / discovery split with max-2-per-creator diversity.
- Explainable recommendations (`generate_reason` UDF).
- Cold start fallback (latest from subscriptions + discovery).
- Multimodal search (image / video / audio file upload → cross-modal scene matching).
- Resilience: size guards on Twelve Labs Embed v2 (35 MB), title-similarity fallback on API failures, frontend decoupled loading so one failing endpoint never blocks the page.

### Open
- Session-based live personalization (re-rank within a session based on in-session clicks).
- Production deployment of the FastAPI backend (frontend is Vercel-ready today).

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
| `download_videos.py` | Fetch MP4 files from YouTube for Pixeltable ingestion |
| `setup_pixeltable.py` | Create schema, ingest, build scene view + embedding indexes |
| `run_setup_logged.sh` | Same, with `pxt.drop_dir` reset + logging to `backend/logs/` |
| `main.py` | Start FastAPI on `:8000` |

## Key Decisions

1. **Dual data source** — Frontend works against Next.js `/api/*` (TL direct) or FastAPI + Pixeltable, toggled by `NEXT_PUBLIC_API_BASE`. Keeps the demo runnable without the backend.
2. **Scene-level retrieval** — `video_scenes` is the primary index; `title_marengo` is the fallback when scene embedding or the Embed API fails. All rec + search paths use both helpers in `backend/routers/videos.py`.
3. **`user_metadata` as source of truth** — Creator / category / upload date live in Twelve Labs, not in local JSON. `scripts/update_tl_metadata.py` writes; runtime only reads.
4. **Analyze as computed columns** — Topic / style / tone run automatically on INSERT, so attribute-based recommendation reasons are always available.
5. **Diversity + hybrid discovery** — 70 / 30 subscription / discovery split with max 2 videos per creator. Prevents the classic filter bubble without abandoning subscribed creators.
6. **Local-first Pixeltable** — `PIXELTABLE_HOME=./data` under `backend/` so other Pixeltable projects on the same machine stay untouched. `pxt.drop_dir(substack_rec)` is the safe reset — never delete `~/.pixeltable`.
7. **Resilience by default** — Twelve Labs rate-limits, 502s, and file-size limits all degrade gracefully to title similarity or empty results rather than 500s or hung frontends.

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
CORS_ORIGINS=http://localhost:3000
PIXELTABLE_HOME=./data                            # Optional: scope Pixeltable to this repo
```

See [`README.md`](./README.md#quick-start) for the full run order.

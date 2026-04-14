# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Commands

```bash
# Frontend
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint (flat config, eslint.config.mjs)
npm start            # Serve production build

# Backend (run from backend/ directory)
uv sync                                # Install deps from lockfile into .venv
uv run download_videos.py              # Download 3 quick-start videos (or --full for all 25)
uv run setup_pixeltable.py             # Load all 25 videos, chunk only downloaded ones
uv run main.py                         # Start FastAPI on :8000
```

No test framework is configured yet.

## Architecture

Substack TV-style video recommendation engine demo. Next.js 16 frontend + FastAPI/Pixeltable backend with Twelve Labs Marengo 3.0 embeddings for semantic recommendations.

```
Pages → src/lib/api.ts → FastAPI backend (backend/) → Pixeltable → TL Embed/Generate APIs
         API_BASE          or Next.js /api/* routes → TL API direct
```

### Frontend

- **Next.js 16** App Router with React 19, TypeScript, Tailwind CSS v4
- Path alias: `@/*` maps to `./src/*`
- All pages in `src/app/` (dynamic routes: `[id]`), all client components
- API routes in `src/app/api/` proxy Twelve Labs API (fallback when no backend)
- Shared components in `src/components/`
- Data layer + types in `src/lib/`
- `NEXT_PUBLIC_API_BASE` env var switches between Next.js routes and FastAPI backend

### Backend (backend/)

- **FastAPI** with Pixeltable as unified data layer
- **`backend/main.py`** — App entry, CORS, lifespan, router includes
- **`backend/config.py`** — Env vars, TL API config, creator descriptions, Analyze prompt
- **`backend/models.py`** — Pydantic models with camelCase serialization matching `types.ts`
- **`backend/download_videos.py`** — Downloads video files from YouTube using yt-dlp Python API (required before setup)
- **`backend/setup_pixeltable.py`** — Schema + data: tables, title embedding index, Analyze API attributes, scene detection (`scene_detect_histogram`), `video_scenes` view (`video_splitter` with `mode='fast'`). Best-effort try/except on scene view.
- **`backend/functions.py`** — `analyze_video` UDF (TL Analyze API), `generate_reason` for rec explanations
- **`backend/routers/videos.py`** — Video endpoints + shared utilities: `_scene_similarity`, `_title_similarity`, `_select_videos`, `_attach_attrs`, `_load_creators_map` (cached 5 min)
- **`backend/routers/`** — creators, recommendations, search (all import shared functions from videos.py)

### Key layers

- **`src/lib/twelve-labs.ts`** — Server-side TL API client; fetches videos from index, maps `user_metadata` to `Video` type
- **`src/lib/api.ts`** — Client-side fetch helpers: `getVideos`, `getVideo`, `getCreators`, `getCreator`, `getForYouRecommendations`, `getSimilarVideos`, `getCreatorCatalog`, `searchVideos`
- **`src/lib/types.ts`** — Core domain types: `Video`, `Creator`, `Recommendation`, `UserState`; `attributes` is optional (populated when Analyze API runs)
- **`src/lib/user-state.tsx`** — React Context for simulated user state (subscriptions + watch history), persisted to localStorage under key `substack-rec-user-state`
- **`src/components/video-player.tsx`** — HLS video player using hls.js

### Routes

| Route | File |
|---|---|
| `/` (Home) | `src/app/page.tsx` |
| `/creator/[id]` | `src/app/creator/[id]/page.tsx` |
| `/watch/[id]` | `src/app/watch/[id]/page.tsx` |
| `/explore` | `src/app/explore/page.tsx` |
| `/search` | `src/app/search/page.tsx` |

### API Routes (Next.js — fallback)

| Route | Source |
|---|---|
| `GET /api/videos` | `src/app/api/videos/route.ts` |
| `GET /api/videos/[id]` | `src/app/api/videos/[id]/route.ts` |
| `GET /api/creators` | `src/app/api/creators/route.ts` |
| `GET /api/creators/[id]` | `src/app/api/creators/[id]/route.ts` |

### API Routes (FastAPI backend)

| Route | Source |
|---|---|
| `GET /api/videos` | `backend/routers/videos.py` |
| `GET /api/videos/:id` | `backend/routers/videos.py` |
| `GET /api/creators` | `backend/routers/creators.py` |
| `GET /api/creators/:id` | `backend/routers/creators.py` |
| `POST /api/recommendations/for-you` | `backend/routers/recommendations.py` |
| `POST /api/recommendations/similar` | `backend/routers/recommendations.py` |
| `POST /api/recommendations/creator-catalog` | `backend/routers/recommendations.py` |
| `GET /api/search?q=` | `backend/routers/search.py` |
| `POST /api/search` (multimodal) | `backend/routers/search.py` |

### Design system

- Dark theme with TwelveLabs brand green (`#00DC82`) accent on warm charcoal background
- Fonts: Instrument Serif (display, `--font-display`), Geist (body, `--font-geist-sans`), Geist Mono (`--font-geist-mono`)
- CSS uses `noise` class on body for texture overlay

### Environment variables

```
# Frontend (.env.local)
TWELVELABS_API_KEY=tlk_...                       # Required
TWELVELABS_INDEX_ID=...                          # Required
NEXT_PUBLIC_API_BASE=http://localhost:8000/api    # Optional: use Pixeltable backend

# Backend (backend/.env)
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
CORS_ORIGINS=http://localhost:3000
```

### Scripts

- `scripts/update_tl_metadata.py` — Uploads creator/category metadata from CSV to TL `user_metadata`
- `scripts/download_and_collect.py` — YouTube download + metadata collection (one-time)
- `scripts/curate_videos.csv` — Curated video list with YouTube IDs

## Current state

Fully implemented. FastAPI + Pixeltable backend with scene-based video indexing. `scene_detect_histogram` finds natural scene boundaries, `video_splitter(mode='fast')` splits at those points (stream copy, no re-encoding), and Marengo 3.0 embeds each scene. All queries (search and recommendations) route through `video_scenes` when available, with `title_marengo` as fallback. Shared `_scene_similarity` / `_title_similarity` in `videos.py` eliminate code duplication. `_select_videos` fetches computed attrs in a single query pass. `_load_creators_map()` cached with 5-min TTL. Quick-start: 3 videos (~4 min setup). Full: 25 videos from TL index with HLS playback, 10 creators. Dependencies: `scenedetect`, `opencv-python-headless`.

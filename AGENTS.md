<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Project guidance

## Commands

```bash
# Frontend
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint (flat config, eslint.config.mjs)
npm start            # Serve production build

# Backend (run from backend/ directory)
uv sync                                          # Install deps from lockfile into .venv
uv run download_videos.py                        # Download 3 quick-start videos (or --full for all 25; add --r2 on cloud hosts)
uv run pxt schema diff app.py substack_rec       # Preview schema changes
uv run pxt schema update app.py substack_rec     # Create or update tables, view, and indexes
uv run load.py                                   # Insert 3 quick-start videos (or --full for all 25)
./run_setup_logged.sh --drop-dir                 # pxt.drop_dir(substack_rec), then schema update, then load.py; logs to backend/logs/setup-*.log
uv run main.py                                   # Start FastAPI on :8000

# Pixeltable reset: use --drop-dir for this app only. Deleting PIXELTABLE_HOME or pgdata wipes *all*
# namespaces in that home (entire embedded DB), not just this repo — use per-project PIXELTABLE_HOME=./data.
```

Focused checks use Node's built-in test runner and Python's unittest:

```bash
node --test tests/catalog.test.mjs
cd backend && uv run python -m unittest discover -s tests
```

## Architecture

Substack TV-style video recommendation engine demo. Next.js 16 frontend + FastAPI/Pixeltable backend with Twelve Labs Marengo 3.0 embeddings for semantic recommendations.

```
Pages → src/lib/api.ts → FastAPI backend (backend/) → Pixeltable → TL Embed/Analyze APIs
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
- **`backend/download_videos.py`** — Downloads video files from YouTube using yt-dlp Python API (required before load)
- **`backend/app.py`** — Class-based schema (`Creators`, `Videos`, `VideoScenes` view), computed columns, and embedding indexes. Applied with `pxt schema update app.py substack_rec`.
- **`backend/load.py`** — Reads title, creator, category, HLS URL, and thumbnail from the TwelveLabs index and inserts rows
- **`backend/functions.py`** — `analyze_video` UDF (TL Analyze API), `embed_video_retry` (Marengo video embedding with retry while TwelveLabs finishes processing an upload), `generate_reason` for rec explanations
- **`backend/routers/videos.py`** — Video endpoints + shared utilities: `_scene_similarity`, `_title_similarity`, `_select_videos`, `_attach_attrs`, `_load_creators_map` (cached 5 min)
- **`backend/routers/`** — creators, recommendations, search (all import shared functions from videos.py)

### Key layers

- **`src/lib/twelve-labs.ts`** — Server-side TL API client; fetches videos from index, maps `user_metadata` to `Video` type
- **`src/lib/api.ts`** — Client-side fetch helpers: `getVideos`, `getVideo`, `getCreators`, `getCreator`, `getForYouRecommendations`, `getSimilarVideos`, `getCreatorCatalog`, `searchVideos`, `searchByFile`
- **`src/lib/types.ts`** — Core domain types: `Video`, `Creator`, `Recommendation`, `UserState`; `attributes` is optional (populated when Analyze API runs)
- **`src/lib/user-state.tsx`** — React Context for simulated user state (subscriptions + watch history), persisted to localStorage under key `curatorai-user-state`
- **`src/components/video-player.tsx`** — HLS video player using hls.js

### Routes

| Route | File |
|---|---|
| `/` (Home) | `src/app/page.tsx` |
| `/creator/[id]` | `src/app/creator/[id]/page.tsx` |
| `/watch/[id]` | `src/app/watch/[id]/page.tsx` |
| `/explore` | `src/app/explore/page.tsx` |
| `/search` | `src/app/search/page.tsx` |
| `/how-it-works` | `src/app/how-it-works/page.tsx` |

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

FastAPI + Pixeltable 0.7.18 backend with class-based schemas in `app.py`. Computed columns store scene cut times and the Analyze API topic, style, and tone; failed Analyze calls leave tags unknown. The `VideoScenes` view splits each video into clips (`video_splitter` with `mode='fast'`), and an unnamed Marengo 3.0 embedding index on `video_segment` covers search and recommendations. A title embedding index is the text fallback. Pixeltable maintains the scene index incrementally on ordinary inserts and deletes. Recommendations reuse stored scene vectors first; text/title fallbacks call TwelveLabs. FastAPI applies the 70/30 subscription/discovery target when candidates permit and caps results at two per creator. The frontend catalog helper follows every backend page. Shared `_scene_similarity` / `_title_similarity` in `videos.py` eliminate code duplication. `_select_videos` fetches computed attrs in a single query pass. `_load_creators_map()` cached with 5-min TTL. Quick-start: 3 videos (~4 min setup). Full: 25 videos from the TL index with HLS playback, 10 creators. Dependencies: `scenedetect`, `opencv-python-headless`.

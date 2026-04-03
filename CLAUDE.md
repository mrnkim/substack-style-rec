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
uv run setup_pixeltable.py             # Create schema + load data from TL index (idempotent)
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
- **`backend/setup_pixeltable.py`** — Schema + data: creates tables, indexes, computed columns, and loads videos from TL index
- **`backend/functions.py`** — `analyze_video` UDF (TL Generate API), `generate_reason` for rec explanations
- **`backend/routers/`** — videos, creators, recommendations, search

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

Fully implemented. 25 videos from Twelve Labs index with HLS playback, 10 creators. FastAPI + Pixeltable backend provides Marengo 3.0 embedding-based recommendations (text embeddings on titles + 1,409 video segment embeddings), Analyze API attribute extraction, semantic search, explainable recommendations with 70/30 subscription/discovery balancing, and creator diversity. See `HANDOFF.md` for full status.

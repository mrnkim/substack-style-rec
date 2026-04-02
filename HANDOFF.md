# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-03-29

## Project Overview

AI-powered video recommendation engine demo in the style of Substack TV. Uses Twelve Labs Marengo embeddings + PixelTable backend for semantic video recommendations.

**Goal**: Demonstrate TwelveLabs' multimodal video understanding for ISV creator platforms (UScreen, Substack, Kajabi) with Netflix-style discovery and personalized recommendations.

## Architecture

```
┌─────────────────────────────┐
│  Frontend (Next.js + TS)    │
│  Deployed on Vercel         │
└──────────┬──────────────────┘
           │ NEXT_PUBLIC_API_BASE
           │ Default: /api (Next.js routes → TL)
           │ PixelTable: http://localhost:8000/api
           ▼
┌─────────────────────────────┐
│  Backend (FastAPI + Python) │  ← backend/ directory
│  • /api/videos, /api/creators
│  • /api/recommendations/*   │
│  • /api/search              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  PixelTable                 │
│  • creators + videos tables │
│  • Marengo 3.0 embedding    │
│    index on title           │
│  • Computed columns:        │
│    topic, style, tone       │
│    (via TL Analyze API)     │
│  • .similarity() search     │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Twelve Labs API            │
│  • Video index (25 videos)  │
│  • Embed API v2 (Marengo)   │
│  • Generate API (Analyze)   │
│  • HLS streaming + thumbs   │
└─────────────────────────────┘
```

## Tech Stack

| Layer | Tech | Notes |
|---|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS | App Router, client components |
| Video Data | Twelve Labs API (index: `69c37b6708cd679f8afbd748`) | 25 videos, HLS streaming, CloudFront thumbnails |
| Video Player | hls.js | HLS streaming playback |
| Backend | FastAPI + PixelTable | `backend/` directory in this repo |
| Embeddings | Twelve Labs Marengo 3.0 (512-dim) | Text embeddings on title via PixelTable |
| Attribute Extraction | Twelve Labs Generate API | Topic, style, tone as computed columns |
| Design System | Strand dark variant | Brand green accent, warm charcoal |
| Deployment | Vercel (FE) + TBD (BE) | |

## Implementation Status

### Phase 1: Foundation (Complete)
- [x] Project scaffolding (Next.js + TS + Tailwind)
- [x] Backend spec for PixelTable team (`docs/BACKEND_SPEC.md`)
- [x] Video curation — 25 YouTube longform videos across 10 creators
- [x] Video download + Twelve Labs indexing (index: `69c37b6708cd679f8afbd748`)
- [x] Creator/category metadata stored in TL `user_metadata`
- [x] Frontend fetches real data from Twelve Labs API via Next.js API routes
- [x] HLS video playback with hls.js
- [x] Real CloudFront thumbnails (not placeholders)
- [x] Cold start fallback for empty watch history
- [x] All 5 pages functional with real data
  - Dark theme, Strand design system (dark variant)
  - Instrument Serif display + Geist body fonts
  - TwelveLabs green (#00DC82) accent

### Phase 2: Core Features — PixelTable Backend (Implemented)
- [x] FastAPI backend scaffolded (`backend/`)
- [x] PixelTable schema: creators + videos tables with Marengo 3.0 embedding index
- [x] Analyze API attribute extraction via computed columns (topic/style/tone)
- [x] Data ingestion script (`backend/ingest.py`) loads from TL index
- [x] All CRUD endpoints: `/api/videos`, `/api/creators` with pagination
- [x] Recommendation engine: `/api/recommendations/for-you` with 70/30 subscription/discovery split
- [x] Similar videos: `/api/recommendations/similar`
- [x] Creator catalog: `/api/recommendations/creator-catalog`
- [x] Semantic search: `/api/search?q=` via `.similarity()`
- [x] Cold start handling (empty watch history fallback)
- [x] Creator diversity filter (max 2 per creator)
- [x] Explainable recommendations with attribute-based reasons
- [x] Frontend API layer updated with recommendation + search helpers
- [ ] Video file re-download (for Phase 2b video segment embeddings)
- [ ] Session-based refinement (live personalization)

### Phase 2b: Video Segment Embeddings (Future)
- [ ] Re-download video files (`backend/download_videos.py`)
- [ ] Add `pxt.Video` column + `video_splitter` segment view
- [ ] Marengo 3.0 video embeddings on 30s segments
- [ ] Upgrade recommendation queries to segment-level similarity

### Phase 3: Polish
- [ ] Responsive design refinements
- [ ] Production deployment

## Data Flow

### Default (Next.js → Twelve Labs)
```
Browser → Next.js API routes → Twelve Labs API
                                 ├─ GET /indexes/{id}/videos (list)
                                 ├─ GET /indexes/{id}/videos/{vid} (detail)
                                 └─ Returns: system_metadata + hls + user_metadata
```

### PixelTable Backend (set NEXT_PUBLIC_API_BASE=http://localhost:8000/api)
```
Browser → FastAPI backend → PixelTable tables + TL Embed/Generate APIs
           ├─ GET  /api/videos, /api/videos/:id
           ├─ GET  /api/creators, /api/creators/:id
           ├─ POST /api/recommendations/for-you
           ├─ POST /api/recommendations/similar
           ├─ POST /api/recommendations/creator-catalog
           └─ GET  /api/search?q=
```

## Twelve Labs Index

- **Index name**: `substack-style-rec`
- **Index ID**: `69c37b6708cd679f8afbd748`
- **Models**: Marengo 3.0 (visual + audio), Pegasus 1.2
- **Addons**: thumbnail
- **Video count**: 25 (19 originally indexed + 6 added later)
- **Total duration**: ~11.6 hours

### user_metadata Schema (per video)

Stored via `scripts/update_tl_metadata.py`:

```json
{
  "youtubeId": "j9Qm6_lEdcQ",
  "creatorId": "UCPD_bxCRGpmmeQcbe2kpPaA",
  "creatorName": "First We Feast",
  "category": "interview",
  "uploadDate": "2025-06-12"
}
```

Future additions (from Analyze API):
```json
{
  "topic": ["food", "celebrity", "challenge"],
  "style": "interview",
  "tone": "playful"
}
```

## Data Model

### Video
```typescript
{
  id: string              // Twelve Labs video_id (not YouTube ID)
  title: string
  creator: Creator
  category: "interview" | "commentary" | "creative" | "educational"
  duration: number        // seconds
  thumbnailUrl: string    // CloudFront URL from TL
  hlsUrl?: string         // HLS streaming URL from TL
  uploadDate: string
  attributes?: {          // Optional — extracted via Analyze API
    topic: string[]
    style: VideoStyle
    tone: VideoTone
  }
}
```

### Creator
```typescript
{
  id: string              // YouTube channel ID
  name: string
  avatarUrl: string
  description: string     // Static, in src/lib/twelve-labs.ts
  videoCount: number      // Computed from video list
}
```

### UserState (client-side, simulated)
```typescript
{
  subscriptions: string[]   // creator IDs (YouTube channel IDs)
  watchHistory: string[]    // video IDs (TL video IDs)
}
```

## API Routes

### Next.js (Twelve Labs direct)

| Method | Route | Source | Description |
|---|---|---|---|
| GET | `/api/videos` | Twelve Labs API | List all videos, optional `?category=` `?creator_id=` |
| GET | `/api/videos/[id]` | Twelve Labs API | Single video detail |
| GET | `/api/creators` | Twelve Labs API | List all creators (derived from videos) |
| GET | `/api/creators/[id]` | Twelve Labs API | Creator detail + video list |

### FastAPI Backend (PixelTable)

| Method | Route | Description |
|---|---|---|
| GET | `/api/videos` | Paginated video list with category/creator filters |
| GET | `/api/videos/:id` | Single video detail |
| GET | `/api/creators` | All creators with video counts |
| GET | `/api/creators/:id` | Creator detail + video list |
| POST | `/api/recommendations/for-you` | 70/30 subscription/discovery recs |
| POST | `/api/recommendations/similar` | Similar videos for watch sidebar |
| POST | `/api/recommendations/creator-catalog` | Creator catalog sorted by relevance |
| GET | `/api/search?q=` | Semantic text-to-video search |
| GET | `/api/health` | Health check |

## Content Inventory

| Creator | Videos | Category |
|---|---|---|
| First We Feast | 3 | interview |
| The Futur | 2 | interview |
| Colin and Samir | 2 | interview |
| The Diary Of A CEO | 3 | interview |
| Mel Robbins | 3 | interview |
| Johnny Harris | 3 | commentary |
| ColdFusion | 3 | commentary |
| Vox | 3 | creative |
| Kirsten Dirksen | 3 | creative |
| 3Blue1Brown | 3 | educational |
| Apple Music | 2 | creative |
| **Total** | **25** | |

Note: 6 videos from CSV (curate_videos.csv lists 31) were not uploaded to the TL index.

## Scripts

| Script | Location | Purpose |
|---|---|---|
| `download_and_collect.py` | `scripts/` | Download YouTube videos + collect metadata CSVs |
| `update_tl_metadata.py` | `scripts/` | Upload creator/category metadata to TL user_metadata |
| `curate_videos.csv` | `scripts/` | Curated video list with YouTube IDs + categories |
| `videos_metadata.csv` | `scripts/` | Video metadata (title, creator, duration, thumbnail) |
| `creators_metadata.csv` | `scripts/` | Creator metadata (name, channel URL, follower count) |
| `CURATION_GUIDE.md` | `scripts/` | Channel suggestions + selection criteria |
| `setup_pixeltable.py` | `backend/` | Create PixelTable schema (tables, indexes, computed columns) |
| `ingest.py` | `backend/` | Load data from TL index into PixelTable |
| `download_videos.py` | `backend/` | Re-download video files for Phase 2b |

## Key Files

| File | Purpose |
|---|---|
| `src/lib/twelve-labs.ts` | Server-side TL API client + video mapping |
| `src/lib/api.ts` | Client-side fetch helpers with recommendation/search support |
| `src/lib/types.ts` | Core TypeScript types |
| `src/lib/user-state.tsx` | Client-side subscription + watch history (localStorage) |
| `src/components/video-player.tsx` | HLS video player (hls.js) |
| `docs/BACKEND_SPEC.md` | Full API spec for PixelTable team |
| `backend/main.py` | FastAPI app entry point |
| `backend/config.py` | Environment configuration + TL API settings |
| `backend/models.py` | Pydantic models matching frontend types.ts |
| `backend/setup_pixeltable.py` | PixelTable schema definition |
| `backend/ingest.py` | Data ingestion from Twelve Labs index |
| `backend/functions.py` | Analyze API UDF + recommendation reason generator |
| `backend/routers/videos.py` | Video CRUD endpoints |
| `backend/routers/creators.py` | Creator CRUD endpoints |
| `backend/routers/recommendations.py` | For-you, similar, creator-catalog endpoints |
| `backend/routers/search.py` | Semantic search endpoint |

## Key Decisions

1. **Dual data source**: Frontend can fetch from Next.js API routes (TL direct) or PixelTable FastAPI backend — controlled by `NEXT_PUBLIC_API_BASE` env var
2. **user_metadata for enrichment**: Creator info, category, uploadDate stored in TL `user_metadata` — single source of truth, no local mapping files
3. **Marengo 3.0 text embeddings (Phase 1)**: Embedding index on video titles enables semantic search and similarity-based recs without video files. Phase 2b adds video segment embeddings.
4. **Analyze API as computed column**: topic/style/tone extracted automatically on video INSERT via TL Generate API
5. **70/30 subscription/discovery**: Recommendation engine balances subscribed creator content with cross-creator discovery
6. **Creator diversity**: Max 2 videos per creator in recommendation results
7. **Cold start fallback**: Empty watch history → latest videos from subscribed creators + discovery
8. **HLS streaming**: Videos play via hls.js using CloudFront HLS URLs from TL
9. **Subscription = simulated**: localStorage-based toggle, no real auth
10. **Design**: Strand design system dark variant — TwelveLabs brand green (#00DC82) on warm charcoal

## Backend Setup

```bash
cd backend
pip install -e .                 # Install dependencies
cp .env.example .env             # Add your TWELVELABS_API_KEY and INDEX_ID
python setup_pixeltable.py       # Create schema
python ingest.py                 # Load data from TL index
python main.py                   # Start FastAPI on :8000
```

Then set `NEXT_PUBLIC_API_BASE=http://localhost:8000/api` in the frontend `.env.local` to use the backend.

## Environment Variables

### Frontend (.env.local)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
NEXT_PUBLIC_API_BASE=http://localhost:8000/api   # Optional: use PixelTable backend
```

### Backend (backend/.env)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
CORS_ORIGINS=http://localhost:3000
```

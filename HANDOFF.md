# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-03-25

## Project Overview

AI-powered video recommendation engine demo in the style of Substack TV. Uses Twelve Labs Marengo embeddings + PixelTable backend for semantic video recommendations.

**Goal**: Demonstrate TwelveLabs' multimodal video understanding for ISV creator platforms (UScreen, Substack, Kajabi) with Netflix-style discovery and personalized recommendations.

## Architecture

```
┌─────────────────────────────┐
│  Frontend (Next.js + TS)    │
│  Deployed on Vercel         │
└──────────┬──────────────────┘
           │ /api/* routes (Next.js)
           │ Currently: Twelve Labs API direct
           │ Future:    PixelTable FastAPI
           ▼
┌─────────────────────────────┐
│  Twelve Labs API            │
│  • Video index (25 videos)  │
│  • HLS streaming + thumbs   │
│  • user_metadata (creator,  │
│    category, uploadDate)    │
│  • Marengo 3.0 embeddings   │
│  • Analyze API (attributes) │
└─────────────────────────────┘
           │
           ▼ (Phase 2)
┌─────────────────────────────┐
│  Backend (FastAPI + Python) │  ← PixelTable team owns this
│  PixelTable = unified data  │
│  (storage + embeddings +    │
│   vector search + pipeline) │
└─────────────────────────────┘
```

## Tech Stack

| Layer | Tech | Notes |
|---|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS | App Router, client components |
| Video Data | Twelve Labs API (index: `69c37b6708cd679f8afbd748`) | 25 videos, HLS streaming, CloudFront thumbnails |
| Video Player | hls.js | HLS streaming playback |
| Backend (future) | FastAPI + PixelTable | PixelTable team implements |
| Embeddings | Twelve Labs Marengo 3.0 | Multimodal (visual + audio) |
| Attribute Extraction | Twelve Labs Analyze API | Topic, style, tone (not yet extracted) |
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

### Phase 2: Core Features (PixelTable Integration)
- [ ] Connect to PixelTable FastAPI backend (swap `API_BASE` in `src/lib/api.ts`)
- [ ] Real Marengo embedding-based recommendations (replace client-side similarity)
- [ ] Analyze API attribute extraction → store in TL `user_metadata`
- [ ] Session-based refinement (live personalization)

### Phase 3: Polish
- [ ] Explainable recommendations with Analyze API attributes
- [ ] Creator diversity filter (max 2 per creator in results)
- [ ] Responsive design refinements
- [ ] Production deployment

## Data Flow

### Current (Phase 1)
```
Browser → Next.js API routes → Twelve Labs API
                                 ├─ GET /indexes/{id}/videos (list)
                                 ├─ GET /indexes/{id}/videos/{vid} (detail)
                                 └─ Returns: system_metadata + hls + user_metadata
```

### Future (Phase 2 — PixelTable)
```
Browser → Next.js API routes → PixelTable FastAPI → PixelTable + TL API
          (swap API_BASE)       ├─ /api/videos
                                ├─ /api/recommendations/*
                                └─ /api/search
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

## API Routes (Next.js)

| Method | Route | Source | Description |
|---|---|---|---|
| GET | `/api/videos` | Twelve Labs API | List all videos, optional `?category=` `?creator_id=` |
| GET | `/api/videos/[id]` | Twelve Labs API | Single video detail |
| GET | `/api/creators` | Twelve Labs API | List all creators (derived from videos) |
| GET | `/api/creators/[id]` | Twelve Labs API | Creator detail + video list |

Future (PixelTable):
| POST | `/api/recommendations/for-you` | PixelTable | Embedding-based recommendations |
| POST | `/api/recommendations/similar` | PixelTable | Similar video sidebar |
| GET | `/api/search?q=` | PixelTable | Semantic search |

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

## Key Files

| File | Purpose |
|---|---|
| `src/lib/twelve-labs.ts` | Server-side TL API client + video mapping |
| `src/lib/api.ts` | Client-side fetch helpers (swap `API_BASE` for PixelTable) |
| `src/lib/types.ts` | Core TypeScript types |
| `src/lib/user-state.tsx` | Client-side subscription + watch history (localStorage) |
| `src/components/video-player.tsx` | HLS video player (hls.js) |
| `docs/BACKEND_SPEC.md` | Full API spec for PixelTable team |

## Key Decisions

1. **Twelve Labs as interim data source**: Videos fetched from TL API via Next.js API routes; swap to PixelTable by changing `API_BASE` in `src/lib/api.ts`
2. **user_metadata for enrichment**: Creator info, category, uploadDate stored in TL `user_metadata` — single source of truth, no local mapping files
3. **attributes optional**: Video attributes (topic, style, tone) will be populated later via Analyze API; UI gracefully hides when absent
4. **HLS streaming**: Videos play via hls.js using CloudFront HLS URLs from TL
5. **Subscription = simulated**: localStorage-based toggle, no real auth
6. **Watch history = click-based**: Entering watch page marks video as watched (TL video IDs)
7. **Cold start fallback**: Empty watch history → latest videos from subscribed creators + discovery
8. **Design**: Strand design system dark variant — TwelveLabs brand green (#00DC82) on warm charcoal

## Handoff to PixelTable Team

> Full spec: `docs/BACKEND_SPEC.md`

Core deliverables for the PixelTable team:
1. **PixelTable schema**: videos table + Marengo embedding index
2. **Computed columns**: Video INSERT triggers segmentation → embedding → attribute extraction pipeline
3. **FastAPI endpoints**: See API table above — frontend already matches these shapes
4. **Recommendation logic**: `.similarity()` based + subscription/diversity filtering
5. **Semantic search**: Text-to-video cross-modal search
6. **Cold start handling**: See `docs/BACKEND_SPEC.md` for fallback logic when watch_history is empty

### Integration Steps
1. PixelTable team deploys FastAPI server
2. Frontend updates `API_BASE` in `src/lib/api.ts` to point to FastAPI URL
3. Add recommendation endpoints (`/api/recommendations/*`) to `src/lib/api.ts`
4. Replace client-side similarity logic with real embedding-based results

## Environment Variables

```
TWELVELABS_API_KEY=tlk_...    # .env.local (gitignored)
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
```

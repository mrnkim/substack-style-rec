# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-03-24

## Project Overview

AI-powered video recommendation engine demo in the style of Substack TV. Uses Twelve Labs Marengo embeddings + PixelTable backend for semantic video recommendations.

**Goal**: Demonstrate TwelveLabs' multimodal video understanding for ISV creator platforms (UScreen, Substack, Kajabi) with Netflix-style discovery and personalized recommendations.

## Architecture

```
┌─────────────────────────────┐
│  Frontend (Next.js + TS)    │
│  Deployed on Vercel         │
└──────────┬──────────────────┘
           │ REST API
           ▼
┌─────────────────────────────┐
│  Backend (FastAPI + Python) │  ← PixelTable team owns this
│  PixelTable = unified data  │
│  (storage + embeddings +    │
│   vector search + pipeline) │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Twelve Labs API            │
│  • Marengo 3.0 embeddings   │
│  • Analyze API (attributes) │
└─────────────────────────────┘
```

## Tech Stack

| Layer | Tech | Notes |
|---|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS | App Router, SSR |
| Backend | FastAPI + PixelTable | PixelTable team implements |
| Embeddings | Twelve Labs Marengo 3.0 | Multimodal (visual + audio + text) |
| Attribute Extraction | Twelve Labs Analyze API | Topic, style, pacing |
| Design System | @twelvelabs/strand (dark variant) | Brand green accent, warm charcoal |
| Deployment | Vercel (FE) + TBD (BE) | |

## Implementation Status

### Phase 1: Foundation (Current)
- [x] Project scaffolding (Next.js + TS + Tailwind)
- [x] Backend spec for PixelTable team (`docs/BACKEND_SPEC.md`)
- [x] Video curation guide + CSV template (`scripts/CURATION_GUIDE.md`)
- [x] Frontend UI with mock data (all 5 pages)
  - Dark theme, Strand design system (dark variant)
  - Instrument Serif display + Geist body fonts
  - TwelveLabs green (#00DC82) accent
- [ ] Video curation — 25-30 YouTube longform videos (in progress)
- [ ] Video download + Twelve Labs indexing

### Phase 2: Core Features
- [ ] Connect frontend to real backend API (replace mock data)
- [ ] Real Marengo embedding-based recommendations
- [ ] Session-based refinement (live personalization)

### Phase 3: Polish
- [ ] Explainable recommendations with Analyze API attributes
- [ ] Creator diversity filter (max 2 per creator in results)
- [ ] Responsive design refinements
- [ ] Production deployment

## Data Model

### Video
```typescript
{
  id: string              // Twelve Labs video_id
  title: string
  creator: Creator
  category: "interview" | "commentary" | "creative" | "educational"
  duration: number        // seconds
  thumbnailUrl: string
  uploadDate: string
  attributes: {           // Extracted via Analyze API
    topic: string[]       // free-form, e.g. ["AI", "robotics", "ethics"]
    style: VideoStyle     // enum: interview|documentary|essay|tutorial|conversation|analysis|performance|explainer
    tone: VideoTone       // enum: serious|casual|playful|contemplative|energetic|analytical
  }
}
```

### Creator
```typescript
{
  id: string
  name: string
  avatarUrl: string
  description: string
  videoCount: number
}
```

### UserState (client-side, simulated)
```typescript
{
  subscriptions: string[]   // creator IDs
  watchHistory: string[]    // video IDs (ordered)
  currentVideo: string | null
}
```

### Recommendation
```typescript
{
  video: Video
  score: number             // similarity score
  reason: string            // "Similar interview style to X"
  attributes: string[]      // matched attributes (2-3)
  source: "subscription" | "discovery"
}
```

## API Endpoints (Backend Spec for PixelTable Team)

> Full spec: `docs/BACKEND_SPEC.md`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/videos` | List all videos (paginated) |
| GET | `/api/videos/:id` | Video detail |
| GET | `/api/creators` | List all creators |
| GET | `/api/creators/:id` | Creator detail + video list |
| POST | `/api/recommendations/for-you` | Generate "For You" recommendations |
| POST | `/api/recommendations/similar` | Similar video recommendations |
| POST | `/api/recommendations/creator-catalog` | Recommendations within a creator's catalog |
| GET | `/api/search?q=` | Semantic video search |

## Video Curation Plan

Content mix per PRD (25-30 videos):

| Category | % | Count | Examples |
|---|---|---|---|
| Interview/Conversation | 40% | 10-12 | Podcasts, interviews, deep conversations |
| Commentary/Analysis | 30% | 7-9 | News analysis, essays, reviews |
| Creative/Performance | 20% | 5-6 | Documentaries, music, performances |
| Educational/How-To | 10% | 2-3 | Tutorials, lectures |

**Selection criteria**:
- English content (Substack TV target audience)
- 10min+ longform
- Creative Commons or Fair Use
- 2-4 videos per creator (to demonstrate cross-creator recommendations)
- Distributed across 8-10 creators

## Subscription System (Simulated)

- Users toggle "Subscribe" on creator profiles
- State persisted in localStorage (demo purposes)
- Subscriptions + watchHistory sent with recommendation requests
- Backend applies 70/30 balancing:
  - 70%: Unwatched videos from subscribed creators, ranked by semantic similarity
  - 30%: Videos from unsubscribed creators, ranked by semantic similarity
- Creator diversity: max 2 per creator in recommendation results

## Frontend Pages

| Route | Description |
|---|---|
| `/` | Homepage — "For You" + "Continue Watching" + "Recently Added" + category rows |
| `/creator/[id]` | Creator page — profile + full catalog grid |
| `/watch/[id]` | Video player + sidebar recommendations |
| `/explore` | Cross-subscription discovery (unsubscribed creators + category browsing) |
| `/search` | Semantic search + topic suggestions + full browse grid |

## Scripts

| Script | Location | Purpose |
|---|---|---|
| `download_script.py` | `/Users/Miranda/Documents/download_YTvideos/` | Download YouTube videos via yt-dlp |
| `upload_to_twelvelabs.py` | `/Users/Miranda/Documents/download_YTvideos/` | Upload + index to Twelve Labs |
| `curate_videos.csv` | `scripts/` | Curated video list (to be filled) |
| `CURATION_GUIDE.md` | `scripts/` | Channel suggestions + selection criteria |

## Key Decisions

1. **Subscription = simulated**: localStorage-based toggle, no real auth
2. **Watch history = click-based**: Entering watch page marks video as watched
3. **Backend = PixelTable team**: FastAPI thin layer, all AI computation in PixelTable computed columns
4. **Content = English longform**: Mirrors Substack TV's actual content distribution
5. **Framework**: Next.js App Router + Server Components (SSR)
6. **Design**: Strand design system dark variant — TwelveLabs brand green (#00DC82) on warm charcoal

## Handoff to PixelTable Team

> Full spec: `docs/BACKEND_SPEC.md`

Core deliverables for the PixelTable team:
1. **PixelTable schema**: videos table + Marengo embedding index
2. **Computed columns**: Video INSERT triggers segmentation → embedding → attribute extraction pipeline
3. **FastAPI endpoints**: See API table above
4. **Recommendation logic**: `.similarity()` based + subscription/diversity filtering
5. **Semantic search**: Text-to-video cross-modal search

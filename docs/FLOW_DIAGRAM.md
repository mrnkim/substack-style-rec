# API Flow Diagram

## Data Preparation (One-time, before demo)

```
curate_videos.csv (video_id, category, notes)
     │
     │  download_and_collect.py
     │  Step 1: yt-dlp --dump-json → extract metadata
     │          (title, duration, upload_date, thumbnail,
     │           channel_name, channel_id, channel_url)
     │  Step 2: yt-dlp download → .mp4 files
     ▼
Outputs:
  ├── downloads/*.mp4                              Local video files
  ├── videos_metadata.csv                          Video-level metadata
  │     (video_id, title, creator_id, creator_name,
  │      category, duration, upload_date, thumbnail_url)
  └── creators_metadata.csv                        Creator-level metadata
        (creator_id, name, channel_url, follower_count,
         description — add manually after)
     │
     │  upload_to_twelvelabs.py                    ⬡ TWELVE LABS API
     │  POST /v1.3/assets (upload)                 ⬡ (direct call)
     │  POST /v1.3/indexes/{id}/indexed-assets     ⬡ (direct call)
     ▼
Twelve Labs Index (Marengo 3.0)                    ⬡ TWELVE LABS
     │
     │  setup_pixeltable.py
     │  INSERT creators from creators_metadata.csv
     │  INSERT videos from videos_metadata.csv
     ▼
PixelTable auto-pipeline:                          ◆ PIXELTABLE
     ├── Store video (managed storage)             ◆ pxt.Video column
     ├── Generate Marengo embedding                ◆ computed column
     │     └── internally calls                    ⬡ TL Embed API
     ├── Extract attributes                        ◆ computed column
     │     └── internally calls                    ⬡ TL Analyze API
     │           → topic, style, pacing, tone
     └── Update pgvector index (automatic)         ◆ PixelTable
```

**Legend:**
- `⬡` = Twelve Labs API (Marengo embedding, Analyze, index/upload)
- `◆` = PixelTable (storage, computed columns, vector index, queries)
- `○` = Frontend only (localStorage, no backend call)

---

## Page-by-Page API Flow

### Homepage (`/`)

```
┌─────────────────────────────────────────────────────────────┐
│  HOMEPAGE                                                    │
│                                                              │
│  ┌─ Hero (featured video) ──────────────────────────────┐   │
│  │  Picked from "For You" results (first item)          │   │
│  │  No separate API call                                 │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ "For You" row ──────────────────────────────────────┐   │
│  │  POST /api/recommendations/for-you                    │   │
│  │  Body: { subscriptions, watch_history, limit: 10 }    │   │
│  │                                                        │   │
│  │  ◆ PIXELTABLE:                                        │   │
│  │  1. Look up pre-computed embeddings for               │   │
│  │     watch_history videos (already stored)              │   │
│  │  2. .similarity() → top 15 candidates                 │   │
│  │     (uses pgvector index, embeddings were              │   │
│  │      generated via ⬡ TL Embed API at insert time)     │   │
│  │  3. Remove watched videos                              │   │
│  │  4. Split: 70% subscribed / 30% discovery              │   │
│  │  5. Max 2 per creator                                  │   │
│  │  6. Generate reason text from stored attributes        │   │
│  │     (attributes were extracted via ⬡ TL Analyze API    │   │
│  │      at insert time — no live API call here)           │   │
│  │                                                        │   │
│  │  ⬡ TL API calls at query time: NONE                   │   │
│  │  Everything was pre-computed at ingestion              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ "Continue Watching" row ────────────────────────────┐   │
│  │  ○ FRONTEND ONLY                                      │   │
│  │  Reads from localStorage watch_history                │   │
│  │  Video details already cached from previous calls     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ "Recently Added" row ───────────────────────────────┐   │
│  │  GET /api/videos?sort=recent&limit=10                 │   │
│  │                                                        │   │
│  │  ◆ PIXELTABLE:                                        │   │
│  │  videos.order_by(videos.upload_date, asc=False)       │   │
│  │       .limit(10).collect()                            │   │
│  │                                                        │   │
│  │  Plain DB query — no TL API, no embeddings            │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ "Deep Dives" row ──────────────────────────────────┐   │
│  │  GET /api/videos?category=interview&limit=10         │   │
│  │                                                       │   │
│  │  ◆ PIXELTABLE: plain filter query                    │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Watch Page (`/watch/[id]`)

```
User clicks video card
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  WATCH PAGE                                                  │
│                                                              │
│  Two API calls fire in parallel:                             │
│                                                              │
│  ┌─ Main Player Area ──────────────────────────────────┐    │
│  │  GET /api/videos/:id                                 │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE: simple row lookup by ID               │    │
│  │  Returns pre-computed attributes (from ⬡ TL Analyze) │    │
│  │                                                       │    │
│  │  ○ FRONTEND: markWatched(id) → localStorage          │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ "Up Next" Sidebar ────────────────────────────────┐     │
│  │  POST /api/recommendations/similar                  │     │
│  │  Body: { video_id, watch_history, limit: 8 }        │     │
│  │                                                      │     │
│  │  ◆ PIXELTABLE:                                      │     │
│  │  1. Look up pre-computed embedding for video_id     │     │
│  │  2. .similarity() → top 12 candidates               │     │
│  │     (pgvector search over ⬡ TL Marengo embeddings)  │     │
│  │  3. Remove watched, max 2 per creator               │     │
│  │  4. Generate reason from stored attributes          │     │
│  │                                                      │     │
│  │  ⬡ TL API calls at query time: NONE                │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Creator Page (`/creator/[id]`)

```
User clicks creator name or avatar
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  CREATOR PAGE                                                │
│                                                              │
│  ┌─ Creator Profile ───────────────────────────────────┐    │
│  │  GET /api/creators/:id                               │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE: row lookup + join to videos table     │    │
│  │  Plain query — no TL API                              │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ "Recommended From This Creator" row ───────────────┐    │
│  │  POST /api/recommendations/creator-catalog           │    │
│  │  Body: { creator_id, watch_history, limit: 20 }      │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE:                                       │    │
│  │  1. Filter to this creator's videos only              │    │
│  │  2. Look up embeddings for watch_history              │    │
│  │  3. .similarity() → rank by user interest             │    │
│  │     (NOT recency — this is the key value prop)        │    │
│  │                                                       │    │
│  │  ⬡ TL API calls at query time: NONE                  │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ○ FRONTEND: Subscribe/Unsubscribe → localStorage           │
└─────────────────────────────────────────────────────────────┘
```

### Explore Page (`/explore`)

```
┌─────────────────────────────────────────────────────────────┐
│  EXPLORE PAGE                                                │
│                                                              │
│  ┌─ "Creators to Explore" grid ────────────────────────┐    │
│  │  GET /api/creators                                   │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE: list all creators                     │    │
│  │  ○ FRONTEND: filter out subscribed (localStorage)    │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ "Beyond Your Subscriptions" row ───────────────────┐    │
│  │  POST /api/recommendations/for-you                   │    │
│  │  Body: { subscriptions: [], watch_history, limit }    │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE: .similarity() with empty subs         │    │
│  │  → 100% discovery mode, pure semantic matching       │    │
│  │                                                       │    │
│  │  ⬡ TL API calls at query time: NONE                  │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ Category rows ─────────────────────────────────────┐    │
│  │  GET /api/videos?category=interview&limit=10         │    │
│  │  GET /api/videos?category=commentary&limit=10        │    │
│  │  GET /api/videos?category=creative&limit=10          │    │
│  │  GET /api/videos?category=educational&limit=10       │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE: plain filter queries (parallelized)   │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Search Page (`/search`)

```
┌─────────────────────────────────────────────────────────────┐
│  SEARCH PAGE                                                 │
│                                                              │
│  ┌─ Search Input ──────────────────────────────────────┐    │
│  │  User types: "interviews about technology policy"    │    │
│  └──────────┬──────────────────────────────────────────┘    │
│             │                                                │
│             ▼                                                │
│  ┌─ Results Grid ──────────────────────────────────────┐    │
│  │  GET /api/search?q=interviews+about+technology       │    │
│  │                                                       │    │
│  │  ◆ PIXELTABLE:                                       │    │
│  │  sim = videos.title.similarity(                       │    │
│  │      string="interviews about technology policy"      │    │
│  │  )                                                    │    │
│  │  videos.order_by(sim, asc=False).limit(10).collect()  │    │
│  │                                                       │    │
│  │  Cross-modal: text query → video embeddings           │    │
│  │  Possible because ⬡ TL Marengo puts text and video   │    │
│  │  in the same embedding space                          │    │
│  │                                                       │    │
│  │  ⬡ TL API calls at query time:                       │    │
│  │  YES — Marengo embeds the query string on-the-fly    │    │
│  │  (this is the ONE place a live TL call happens)      │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ Empty State ───────────────────────────────────────┐    │
│  │  ○ FRONTEND: show topic pills                        │    │
│  │  + GET /api/videos (browse all)                      │    │
│  │  ◆ PIXELTABLE: plain list query                      │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete API Call Summary

| Page | Endpoint | Who Does the Work | Live TL API Call? |
|---|---|---|---|
| Homepage | `POST /api/recommendations/for-you` | ◆ PixelTable `.similarity()` | No (pre-computed) |
| Homepage | `GET /api/videos?sort=recent` | ◆ PixelTable plain query | No |
| Homepage | `GET /api/videos?category=X` | ◆ PixelTable plain filter | No |
| Homepage | Continue Watching | ○ Frontend localStorage | No |
| Watch | `GET /api/videos/:id` | ◆ PixelTable row lookup | No |
| Watch | `POST /api/recommendations/similar` | ◆ PixelTable `.similarity()` | No (pre-computed) |
| Watch | Mark watched | ○ Frontend localStorage | No |
| Creator | `GET /api/creators/:id` | ◆ PixelTable row lookup + join | No |
| Creator | `POST /api/recommendations/creator-catalog` | ◆ PixelTable `.similarity()` | No (pre-computed) |
| Creator | Subscribe toggle | ○ Frontend localStorage | No |
| Explore | `GET /api/creators` | ◆ PixelTable list query | No |
| Explore | `POST /api/recommendations/for-you` | ◆ PixelTable `.similarity()` | No (pre-computed) |
| Explore | `GET /api/videos?category=X` ×4 | ◆ PixelTable plain filter | No |
| Search | `GET /api/search?q=...` | ◆ PixelTable `.similarity()` | **Yes** — ⬡ TL embeds query |

## When Does Twelve Labs API Get Called?

```
⬡ TWELVE LABS API CALLS
═══════════════════════════════════════════════════════════

AT INGESTION TIME (one-time, setup):
  ├── Upload API        POST /v1.3/assets
  ├── Index API         POST /v1.3/indexes/{id}/indexed-assets
  ├── Embed API         Marengo 3.0 → 512-dim vector per video
  └── Analyze API       → topic, style, pacing, tone per video

  These happen ONCE per video via PixelTable computed columns.
  Results are stored permanently in PixelTable.

AT QUERY TIME (live, per user request):
  └── Embed API         ONLY for search queries
                        "interviews about technology" → 512-dim vector
                        Then PixelTable does pgvector similarity

  Recommendation endpoints (.similarity() on video embeddings)
  use ONLY pre-computed vectors. No live TL call.
```

## System Responsibilities

```
┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐
│  ○ FRONTEND          │  │  ◆ PIXELTABLE        │  │  ⬡ TWELVE LABS       │
│     (Next.js)        │  │     (Python)         │  │     (External API)   │
│                      │  │                      │  │                      │
│  Subscription state  │  │  Video storage       │  │  Marengo 3.0         │
│  Watch history       │  │  Computed columns    │  │   embeddings         │
│  UI rendering        │  │  pgvector index      │  │  Analyze API         │
│  Navigation          │  │  .similarity()       │  │   attribute extract  │
│  Animations          │  │  Filter / sort       │  │  Upload / Index      │
│                      │  │  70/30 balancing     │  │                      │
│  Sends subs +        │  │  Creator diversity   │  │  Called at ingest    │
│  history with each   │  │  Reason generation   │  │  Called at search    │
│  API request         │  │  Thin FastAPI layer   │  │  NOT called for     │
│                      │  │                      │  │  recommendations     │
│  Zero AI             │  │  Orchestrates AI     │  │  Provides AI         │
└─────────────────────┘  └─────────────────────┘  └──────────────────────┘
```

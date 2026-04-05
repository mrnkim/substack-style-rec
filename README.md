# Substack TV-Style Video Recommendation Engine

A production-ready demo of Netflix-style video discovery for creator platforms, powered by [Twelve Labs](https://www.twelvelabs.io/) multimodal video understanding and [Pixeltable](https://www.pixeltable.com/) declarative data infrastructure.

**[Read the tutorial: Building Cross-Modal Video Search with TwelveLabs and Pixeltable](https://www.twelvelabs.io/blog/twelve-labs-and-pixeltable)**

## What this demonstrates

Creator platforms like Substack TV, UScreen, and Kajabi need recommendation engines that understand *what's actually in a video* -- not just titles and tags. This demo shows how Twelve Labs Marengo 3.0 embeddings and Pixeltable's `.similarity()` API deliver:

- **Semantic recommendations** -- "How to legislate AI" surfaces "Are We Really Ready for AI Coding?" (score: 0.64) across different creators, without shared tags
- **Explainable suggestions** -- "Because you watched 'How to legislate AI' -- Similar interview format, Matching serious tone, Discover a new creator"
- **Cross-creator discovery** -- Search "music culture" returns Vox Earworm videos about jazz, Stravinsky, and fade-outs -- semantic understanding, not keyword matching
- **70/30 subscription/discovery balance** -- Familiar content from creators you follow, blended with algorithmically-surfaced new voices

## How it works

```
Next.js Frontend (localhost:3000)
       |
       |  NEXT_PUBLIC_API_BASE
       v
FastAPI Backend (localhost:8000)
  ├── GET  /api/videos, /api/creators
  ├── POST /api/recommendations/for-you    ← 70/30 sub/discovery, diversity, explainable
  ├── POST /api/recommendations/similar    ← watch page sidebar
  ├── POST /api/recommendations/creator-catalog
  └── GET  /api/search?q=                  ← semantic text-to-video search
       |
       v
Pixeltable
  ├── creators table (10 creators)
  ├── videos table (25 videos + computed topic/style/tone)
  ├── Marengo 3.0 title embedding index (25 × 512-dim vectors)
  └── video_segments view (1,409 × 30s segments with video embeddings)
       |
       v
Twelve Labs API
  ├── Embed API v2 → Marengo 3.0 multimodal vectors
  └── Analyze API  → topic, style, tone extraction
```

### Why Pixeltable

[Pixeltable](https://docs.pixeltable.com/) is the data layer that makes this possible with minimal code:

- **Declarative schema** -- Define tables, computed columns, and embedding indexes. Pixeltable handles the rest.
- **Automatic pipelines** -- INSERT a video row and embeddings + attribute extraction run automatically as computed columns. No orchestration code.
- **`.similarity()` API** -- One-line semantic search across the entire corpus: `videos.title.similarity(string="AI technology")`. Powered by pgvector under the hood.
- **Video segmentation** -- `video_splitter(duration=30)` creates a view of 30-second segments, each with its own Marengo embedding. One line of code for 1,409 searchable video chunks.

See the [Pixeltable + Twelve Labs integration docs](https://docs.pixeltable.com/sdk/latest/twelvelabs) for the full API reference.

### Why Twelve Labs Marengo 3.0

[Marengo 3.0](https://www.twelvelabs.io/product/embed) creates a unified semantic space where text, images, audio, and video can all be used interchangeably as search queries:

- **512-dimensional embeddings** that capture visual content, speech, audio, and on-screen text
- **Cross-modal search** -- query with text, get back video segments ranked by actual content similarity
- **Analyze API** -- structured attribute extraction (topic, style, tone) from video content for explainable recommendations

## Content

25 longform creator videos across 10 creators and 4 categories:

| Category | Creators | Videos |
|---|---|---|
| Interview | First We Feast, The Futur, Colin & Samir, Diary of a CEO, Mel Robbins | 13 |
| Commentary | Johnny Harris, ColdFusion | 6 |
| Creative | Vox, Kirsten Dirksen, Apple Music | 8 |
| Educational | 3Blue1Brown | 3 |

## Quick start

### Prerequisites

- Node.js 18+
- Python 3.10+
- A [Twelve Labs API key](https://playground.twelvelabs.io/)

### 1. Frontend

```bash
npm install
npm run dev                    # localhost:3000
```

### 2. Backend

```bash
cd backend

# Add your credentials
cat > .env.local << 'EOF'
TWELVELABS_API_KEY=tlk_your_key_here
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
EOF

uv sync                        # Install deps from lockfile
uv run setup_pixeltable.py     # Create schema + load data from TL index
uv run main.py                 # FastAPI on localhost:8000
```

### 3. Connect frontend to backend

Add to the root `.env.local`:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

That's it. Two commands to set up the backend (`uv sync` + `uv run setup_pixeltable.py`), one to start it.

## Features

| Feature | Endpoint | How it works |
|---|---|---|
| **Personalized "For You"** | `POST /recommendations/for-you` | Marengo `.similarity()` on watch history, 70% subscription / 30% discovery, max 2 per creator |
| **Similar Videos** | `POST /recommendations/similar` | Sidebar recs based on current video's embedding |
| **Creator Catalog** | `POST /recommendations/creator-catalog` | Relevance-sorted (not recency) with `{ recommended, popular }` |
| **Semantic Search** | `GET /search?q=` | Cross-modal text-to-video via `.similarity(string=q)` |
| **Explainable Recs** | All rec endpoints | "Because you watched X -- Similar Y format, Matching Z tone" |
| **Cold Start** | `POST /recommendations/for-you` | Latest from subscriptions + discovery when no watch history |
| **Attribute Extraction** | Computed columns | topic/style/tone via TL Analyze API, runs automatically on INSERT |

## Project structure

```
├── src/                          # Next.js frontend
│   ├── app/                      # Pages: /, /explore, /search, /watch/:id, /creator/:id
│   ├── lib/api.ts                # API client (8 fetch helpers)
│   ├── lib/types.ts              # Video, Creator, Recommendation, UserState
│   └── components/               # VideoCard, VideoRow, VideoPlayer, etc.
│
├── backend/                      # FastAPI + Pixeltable
│   ├── main.py                   # App entry, CORS, routers
│   ├── config.py                 # Environment + TL credentials
│   ├── models.py                 # Pydantic models (camelCase JSON)
│   ├── functions.py              # analyze_video UDF + generate_reason
│   ├── setup_pixeltable.py       # Schema + data: tables, indexes, computed columns, TL ingest
│   └── routers/                  # videos, creators, recommendations, search
│
├── scripts/                      # Content curation + metadata CSVs
└── docs/BACKEND_SPEC.md          # Full API specification
```

## Learn more

- [Building Cross-Modal Video Search with TwelveLabs and Pixeltable](https://www.twelvelabs.io/blog/twelve-labs-and-pixeltable) -- Tutorial on the integration pattern used in this project
- [Pixeltable Twelve Labs SDK Reference](https://docs.pixeltable.com/sdk/latest/twelvelabs) -- `embed()` UDF signatures for text, image, audio, and video
- [Working with Twelve Labs in Pixeltable](https://docs.pixeltable.com/howto/providers/working-with-twelvelabs) -- Step-by-step guide with runnable notebook
- [Twelve Labs Embed API](https://www.twelvelabs.io/product/embed) -- Marengo 3.0 multimodal embeddings
- [Pixeltable Documentation](https://docs.pixeltable.com/) -- Tables, computed columns, embedding indexes, similarity search

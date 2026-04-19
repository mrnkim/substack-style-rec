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
  ├── GET  /api/search?q=                  ← semantic text-to-video search
  └── POST /api/search                    ← multimodal: image/video/audio upload
       |
       v
Pixeltable
  ├── creators table (11 creators)
  ├── videos table (25 videos + pxt.Video + scene detection + topic/style/tone)
  ├── video_scenes view (scene_detect_histogram + video_splitter mode=fast)
  ├── scene_marengo embedding index (multimodal video content per scene)
  └── title_marengo embedding index (text fallback)
       |
       v
Twelve Labs API
  ├── Embed API v2 → Marengo 3.0 multimodal vectors   (via Pixeltable TL integration)
  └── Analyze API  → topic, style, tone extraction    (direct HTTP, wrapped as a Pixeltable UDF)
```

Two integration patterns, one data plane — see [Integration patterns](#integration-patterns) below.

### Why Pixeltable

[Pixeltable](https://docs.pixeltable.com/) is the data layer that makes this possible with minimal code:

- **Declarative schema** -- Define tables, computed columns, and embedding indexes. Pixeltable handles the rest.
- **Automatic pipelines** -- INSERT a video row and embeddings + attribute extraction run automatically as computed columns. No orchestration code.
- **Scene detection** -- `scene_detect_histogram()` automatically finds natural scene boundaries. `video_splitter(mode='fast')` splits at those points with stream copy (no re-encoding). Each scene gets its own Marengo 3.0 embedding.
- **`.similarity()` API** -- One-line cross-modal search: `video_scenes.video_segment.similarity(string="AI technology")` finds videos by actual scene content. Powered by pgvector under the hood.
- **`pxt.Video` column** -- Store video files directly in the table. Scene detection + embedding run automatically as computed columns on insert.

See the [Pixeltable + Twelve Labs integration docs](https://docs.pixeltable.com/sdk/latest/twelvelabs) for the full API reference.

### Why Twelve Labs Marengo 3.0

[Marengo 3.0](https://www.twelvelabs.io/product/embed) creates a unified semantic space where text, images, audio, and video can all be used interchangeably as search queries:

- **512-dimensional embeddings** that capture visual content, speech, audio, and on-screen text
- **Cross-modal search** -- query with text, get back video segments ranked by actual content similarity
- **Analyze API** -- structured attribute extraction (topic, style, tone) from video content for explainable recommendations

### Integration patterns

This backend deliberately uses both of Pixeltable's interop modes against the same provider, so you can see what each looks like side-by-side:

| Pattern | Used for | Where it lives | What it looks like |
|---|---|---|---|
| **Pixeltable integration** (declarative) | Embed API v2 (Marengo 3.0) | `backend/setup_pixeltable.py` | `from pixeltable.functions.twelvelabs import embed` → `videos.add_embedding_index(..., string_embed=embed.using(model_name="marengo3.0"))`. Pixeltable handles auth, batching, retries, and rerunning on new rows. |
| **Bring-your-own API** (direct HTTP, wrapped as a UDF) | Analyze API | `backend/functions.py` | `@pxt.udf def analyze_video(...)` calls `https://api.twelvelabs.io/v1.3/analyze` with `httpx` and returns a dict. Pixeltable still schedules it as a computed column so the output (topic / style / tone) is cached on the row. |

**Why the split is not just cosmetic.** Pixeltable ships a first-class [Twelve Labs integration](https://docs.pixeltable.com/sdk/latest/twelvelabs) for the Embed API, so we use it — one line replaces dozens of lines of batching, retry, and vector-persistence code. The Analyze API does not have a Pixeltable helper yet (it's tied to the per-video index abstraction, not a stateless model call), so we drop down to raw HTTP and wrap it in a UDF. Either way the result is a computed column: if you INSERT a new video, both the embedding index *and* `raw_attributes` recompute automatically, regardless of which pattern produced them.

This is the thing to steal from this repo if you're evaluating Pixeltable: integrations give you the fast path for anything supported, and the `@pxt.udf` escape hatch covers the rest without abandoning the declarative model.

## Content

25 longform videos indexed in Twelve Labs, drawn from a curated set of 30 across 11 creators and 4 categories (`scripts/curate_videos.csv`):

| Category | Creators | Curated |
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
uv run download_videos.py      # Download 3 quick-start videos (~2 min)
uv run setup_pixeltable.py     # Schema + scene detection + Marengo embeddings (~4 min)
uv run main.py                 # FastAPI on localhost:8000

# Logged re-run (pxt.drop_dir on `substack_rec` only — not a full DB wipe; saves `backend/logs/setup-*.log`):
#   ./run_setup_logged.sh --drop-dir
#   ./run_setup_logged.sh --drop-dir --full
# Use `PIXELTABLE_HOME=./data` in backend/.env so other Pixeltable projects under ~/.pixeltable stay safe.

# For the full 25-video dataset (13GB download, ~30 min setup):
uv run download_videos.py --full
uv run setup_pixeltable.py --full
```

### 3. Connect frontend to backend

Add to the root `.env.local`:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

Without this, the browser talks to the Next.js `/api/*` routes instead of FastAPI + Pixeltable, so behavior will not match the backend docs.

### Run order (follow once per machine)

1. **Backend env** — `backend/.env.local` with `TWELVELABS_API_KEY` and `TWELVELABS_INDEX_ID` (`backend/.env` also works; `config.py` reads both). Optional: `PIXELTABLE_HOME=./data` so Pixeltable data lives under `backend/data/`.
2. **Install & load data** — From `backend/`: `uv sync`, then `uv run download_videos.py` (or `--full`), then `uv run setup_pixeltable.py` (matching `--full` if you used it). Skipping download/setup leaves empty tables or no `video_scenes` view.
3. **Root env** — Repo root `.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000/api` as above.
4. **Run two processes** — Terminal A: `cd backend && uv run main.py` (port 8000). Terminal B: repo root `npm run dev` (port 3000).

Quick-start uses 3 short videos for fast iteration (~4 min total setup). Pass `--full` to load all 25 videos with scene detection and Marengo embeddings.

## Deployment (Render + Vercel)

The repo ships a [`render.yaml`](./render.yaml) Blueprint for the backend and a stock Next.js setup for Vercel. End result: frontend on `*.vercel.app` talking to a FastAPI + Pixeltable service on `*.onrender.com`.

### The one thing to understand first

Pixeltable is **stateful**. It runs an embedded Postgres (`pixeltable_pgserver`) that writes to `PIXELTABLE_HOME`, plus video files on local disk. Render web services have an **ephemeral filesystem by default**, so the backend service needs a **[Render Persistent Disk](https://render.com/docs/disks)** mounted at `PIXELTABLE_HOME`. Without it you'd re-run the ~30-minute `setup_pixeltable.py --full` on every deploy and re-burn Twelve Labs Analyze credits. The Blueprint handles this — don't strip the `disk:` block.

### 1. Backend → Render

**Files that ship with the repo:**

- [`backend/Dockerfile`](./backend/Dockerfile) — Python 3.13 + ffmpeg + libgl + `uv`, production `uvicorn` launch, `PIXELTABLE_HOME=/var/pixeltable`.
- [`backend/.dockerignore`](./backend/.dockerignore) — keeps `video_files/`, `data/`, `logs/`, `.venv/` out of the build context.
- [`render.yaml`](./render.yaml) — web service + 20 GB persistent disk mounted at `/var/pixeltable`, Oregon region, `healthCheckPath: /health`.

**Deploy:**

1. Render Dashboard → **New → Blueprint** → pick this repo. Render reads `render.yaml` and proposes the service + disk.
2. Fill the two `sync: false` env vars when prompted:
   - `TWELVELABS_API_KEY = tlk_...`
   - `CORS_ORIGINS = https://your-project.vercel.app` (comma-separate if you have more than one; preview URLs are already allowed via the `*.vercel.app` regex in [`backend/main.py`](./backend/main.py)).
3. First deploy takes ~5 min (Docker build + boot). `GET /health` returns `{"status":"ok"}` as soon as the process is up, even before data is loaded.
4. **One-time data load**: open the Render **Shell** tab on the service and run:
   ```bash
   uv run download_videos.py --full
   uv run setup_pixeltable.py --full
   ```
   This writes pgdata + video files to `/var/pixeltable`, which persists across redeploys. Drop `--full` for the 3-video quick-start (~4 min vs ~30 min).
5. Subsequent deploys just reconnect (`lifespan` in `main.py` logs "Connected to Pixeltable schema") — setup does **not** re-run.

Verify:
```bash
curl https://substack-rec-api.onrender.com/api/videos | jq '.data | length'   # → 25
```

### 2. Frontend → Vercel

1. `vercel link` (or import the repo in the dashboard). Root directory = repo root, framework = Next.js (auto-detected).
2. Project Settings → Environment Variables, same values in Production + Preview + Development:
   ```
   NEXT_PUBLIC_API_BASE = https://substack-rec-api.onrender.com/api
   TWELVELABS_API_KEY   = tlk_...        # used only by the /api/* Next.js fallback
   TWELVELABS_INDEX_ID  = 69c37b6708cd679f8afbd748
   ```
3. Push → PR → preview URL → promote to production.

`NEXT_PUBLIC_API_BASE` is inlined at build time, so changing it requires a redeploy — not a runtime toggle. Leave it unset if you want previews to fall back to the Next.js `/api/*` routes (useful while the backend is still loading data).

### 3. Verification after both sides are live

1. Frontend URL → DevTools Network tab → home page should hit `onrender.com/api/recommendations/for-you`, **not** the Vercel origin. If you see the latter, `NEXT_PUBLIC_API_BASE` didn't propagate — redeploy.
2. CORS: Vercel preview URLs work automatically; a custom domain needs to be added to `CORS_ORIGINS` in Render.

### Alternatives worth naming

- **Fly.io** instead of Render — volumes are first-class and reattach automatically, no cold-start sleep on the hobby plan. `fly launch` from `backend/` with this Dockerfile, `fly volumes create pxt_data --size 20`, `fly deploy`.
- **Railway** — also has volumes; similar pattern.

The disk-vs-no-disk decision is what you're choosing. Everything else is plumbing.

## Features

| Feature | Endpoint | How it works |
|---|---|---|
| **Personalized "For You"** | `POST /recommendations/for-you` | Marengo `.similarity()` on watch history, 70% subscription / 30% discovery, max 2 per creator |
| **Similar Videos** | `POST /recommendations/similar` | Sidebar recs based on current video's embedding |
| **Creator Catalog** | `POST /recommendations/creator-catalog` | Relevance-sorted (not recency) with `{ recommended, popular }` |
| **Semantic Search** | `GET /search?q=` | Text-to-video via scene embeddings `.similarity(string=q)` |
| **Multimodal Search** | `POST /search` | Image/video/audio file upload → cross-modal scene matching |
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
│   ├── download_videos.py        # Download video files from YouTube via yt-dlp (3 default, --full for all)
│   ├── setup_pixeltable.py       # Schema + scene detection + Marengo embeddings + TL ingest
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

# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-06-08
>
> This file is a short, current snapshot. Canonical docs:
> - **Setup & quick start** → [`README.md`](./README.md)
> - **Backend API spec** → [`docs/BACKEND_SPEC.md`](./docs/BACKEND_SPEC.md)
> - **Agent guide** → [`CLAUDE.md`](./CLAUDE.md)

---

## Session Log — 2026-06-08 (PR #14 merge + production deploy of video-to-video)

**Goal of the day:** Merge Pierre's PR #14 (real video-to-video recommendations via scene embeddings, replacing the silent title-only fallback) and get it working live on Render + Vercel.

**Outcome: ✅ video-to-video recommendations are LIVE and verified.**
Example (live `/api/recommendations/similar` on the homestead video):
`Nordic homestead 0.796`, `underground home 0.745` — content-matched via Marengo scene embeddings, not title text.

### What was done
1. **PR #14 merged.** It was a cross-repo PR from `pierrebrunelle:updates` → `mrnkim:main`. Resolved the one conflict (`src/lib/api.ts`: kept BOTH the `withCache` wrapper and `dedupeById`/`dedupeRecs` — dedupe runs inside each cache callback). Fast-forwarded `main` to `230e00e`, closed PR #14 with a merge comment (cross-repo PRs don't auto-close).
2. **Added `curl` to the Docker image** (`6c8d00e`) — `download_videos.py --r2` shells out to `curl`, which the slim base image lacked.
3. **Rebuilt the scene pipeline on Render** (the deployed DB had the embedding index missing AND old `fps=2` scenes):
   - Dropped old `video_scenes` view + `scenes` column, re-downloaded 25 videos (`--r2 --full`), recomputed `scene_detect_histogram(fps=1, threshold=0.9, min_scene_len=900)` → **476 scenes** (vs old 1707), rebuilt the `scene_marengo` embedding index.

### Deployment facts (Render)
- Service: **`substack-rec-api`**, SSH `srv-d7o1sj77f7vs7384ad70@ssh.oregon.render.com`, public URL **`https://substack-rec-api-q2ui.onrender.com`**
- Frontend (Vercel): **`https://substack-style-rec.vercel.app`**, `CORS_ORIGINS=https://substack-style-rec.vercel.app` (correct)
- `PIXELTABLE_HOME=/var/pixeltable` is the **persistent disk** (survives redeploys: pgdata + scene media). `/app` is **ephemeral** (wiped on every redeploy/restart — including `/app/video_files` and `/tmp`).
- **Currently on Pro (4GB)** — was bumped from Standard (2GB) for the index build.

### ⚠️ Hard-won gotchas (read before touching the Render box again)
1. **Embedding-index build OOMs on 2GB.** Pixeltable decodes scene segments into RAM before embedding. Default `ExprEvalNode.MAX_BUFFERED_ROWS=2048` loads all 476 at once → >2GB → Render kills the container (shows as silent death, `oom_kill=0` because it's Render's own memory limit, not the Linux OOM killer). Fix used: bumped to **4GB** and monkeypatched `MAX_BUFFERED_ROWS=64` → built in 454s, peak 3.5GB. `MAX_BUFFERED_ROWS=4` *stalls* the pipeline; 64 is the working/safe value at 4GB. **This memory fix is NOT in code yet — see follow-ups.**
2. **Changing the Render instance type breaks Postgres.** Going 2GB→4GB changed the uid Postgres runs as (data was owned by uid 1000, new instance ran pg as `pgserver` uid 1001) → `pg_ctl` fails with `could not open lock file ... Permission denied` → whole DB down → app 500s → frontend shows CORS errors (no headers on failed responses). **Fix:** `chown -R pgserver:pgserver /var/pixeltable/pgdata` + remove stale `.s.PGSQL.5432` socket and `.s.PGSQL.5432.lock`, then restart the app (`kill -TERM 1` → Render restarts the container). Scaling **back down to 2GB will likely re-break this** (ownership flips again).
3. **Long jobs over SSH must use `setsid`** — Render kills SSH-spawned processes when the session drops, *unless* fully detached (`setsid bash -c "..." </dev/null &`).
4. **Killed Pixeltable processes leave stale Postgres locks** (`idle in transaction`) that block ALL subsequent DB ops, including the live app. Clean with `pg_terminate_backend(pid)` on `state like '%transaction%'`.
5. `scene_detect_histogram` on all 25 videos (~11.6h of footage) takes **~102 min single-threaded** on this box. `add_embedding_index` over 476 scenes takes ~8 min at `MAX_BUFFERED_ROWS=64`.

### Follow-ups / open
- **Scale Render back to 2GB** (serving fits in 2GB; only the build needed 4GB). Expect Postgres ownership to break on the switch — re-apply gotcha #2.
- **Code-ify the memory fix:** make `setup_pixeltable.py`'s `add_embedding_index` honor a low `MAX_BUFFERED_ROWS` (env-configurable) so a future re-setup doesn't OOM on 2GB. Currently a manual monkeypatch only.
- Verify the Vercel frontend renders the recommendations end-to-end (backend API confirmed working post-restart).

---

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

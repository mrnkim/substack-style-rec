# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-04-28
>
> This file is a short, current snapshot. Canonical docs:
> - **Setup & quick start** → [`README.md`](./README.md)
> - **Backend API spec** → [`docs/BACKEND_SPEC.md`](./docs/BACKEND_SPEC.md)
> - **Agent guide** → [`CLAUDE.md`](./CLAUDE.md)

## Project Overview

AI-powered video recommendation demo in the style of Substack TV. Uses Twelve Labs Marengo 3.0 embeddings + Pixeltable for semantic, explainable, cross-creator recommendations.

**Goal**: Demonstrate TwelveLabs multimodal video understanding for ISV creator platforms (Substack, UScreen, Kajabi) with Netflix-style discovery.

## Architecture

```
Next.js 16 frontend (Vercel: substack-style-rec.vercel.app)
       |  NEXT_PUBLIC_API_BASE
       v
FastAPI backend (Render: substack-rec-api-g2ui.onrender.com)
       |
       v
Pixeltable (embedded PostgreSQL on Render persistent disk)
  ├── creators table (10 creators)
  ├── videos table (25 indexed videos + Analyze API attrs)
  └── title_marengo embedding index (text similarity)
       |
       v
Twelve Labs API (Embed v2, Analyze, Search)
       |
Cloudflare R2 (video file storage: tl-substack-style-app bucket)
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
| Scene Search | Twelve Labs Search API (returns scene-level timestamps) |
| Video Player | hls.js with CloudFront HLS URLs from Twelve Labs |
| Video Storage | Cloudflare R2 (`tl-substack-style-app` bucket, public) |
| DB Storage | Embedded Pixeltable Postgres on Render persistent disk (20 GB) |
| Deployment | Vercel (frontend) + Render Starter (backend, $12/mo) |

## Implementation Status

### Complete
- Pixeltable schema: creators + videos tables with title-level Marengo 3.0 embeddings.
- Analyze API computed columns: topic, style, tone run automatically on INSERT.
- All endpoints: `/api/videos`, `/api/creators`, `/api/recommendations/{for-you,similar,creator-catalog}`, `/api/search`.
- 70 / 30 subscription / discovery split with max-2-per-creator diversity.
- Explainable recommendations: short reason + matchedAttributes as individual pills (topic overlap, style/tone, creator context).
- Cold start fallback (latest from subscriptions + discovery).
- Text search via Twelve Labs Search API with scene-level timestamps and scene thumbnails.
- Search results show rank badge, scene time range, category pill, and matched scene thumbnail.
- Nav: Subscriptions dropdown (count + list + unsubscribe) and Watch History dropdown (thumbnails + reset).
- Console logging of recommendation scores for debugging (browser DevTools).
- Video player supports `?t=` query param for scene-level deep linking.
- Resilience: title-similarity fallback on API failures, frontend decoupled loading.
- Production deployment: Vercel (frontend) + Render (backend) + Cloudflare R2 (video files).
- Video download from R2 instead of YouTube (YouTube blocks data center IPs).

### Open / Known Issues
- **video_scenes view not created on Render** — Starter plan (0.5 CPU, 512 MB) cannot run scene_detect_histogram on 25 videos. Text search uses TL Search API as workaround. Recommendations use title_marengo fallback.
- **Render Starter auto-sleep** — 15 min inactivity causes ~30s cold start. Hit `/health` before demos.
- **Multimodal file search disabled** — Image/video/audio upload search removed from UI (requires video_scenes view). Backend code preserved for future re-enablement.
- Session-based live personalization (re-rank within a session based on in-session clicks).
- Scene detection could be re-enabled with Standard plan ($25/mo) or by pre-computing on a local machine and uploading the DB.

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
| `download_videos.py` | Fetch video files from Cloudflare R2 for Pixeltable ingestion |
| `setup_pixeltable.py` | Create schema, ingest, build scene view + embedding indexes |
| `run_setup_logged.sh` | Same, with `pxt.drop_dir` reset + logging to `backend/logs/` |
| `main.py` | Start FastAPI on `:8000` |

## Key Decisions

1. **Dual data source** — Frontend works against Next.js `/api/*` (TL direct) or FastAPI + Pixeltable, toggled by `NEXT_PUBLIC_API_BASE`. Keeps the demo runnable without the backend.
2. **TL Search API for text search** — Text search calls Twelve Labs Search API directly (returns scene-level timestamps + thumbnails). Falls back to Pixeltable title_marengo similarity when TL API is unavailable or for creator-filtered queries.
3. **Recommendations via Pixeltable** — For-you / similar / creator-catalog still use Pixeltable title_marengo embeddings for similarity. TL Search API is only used for the search endpoint.
4. **`user_metadata` as source of truth** — Creator / category / upload date live in Twelve Labs, not in local JSON. `scripts/update_tl_metadata.py` writes; runtime only reads.
5. **Analyze as computed columns** — Topic / style / tone run automatically on INSERT, so attribute-based recommendation reasons are always available.
6. **Diversity + hybrid discovery** — 70 / 30 subscription / discovery split with max 2 videos per creator. Prevents the classic filter bubble without abandoning subscribed creators.
7. **Reason + attributes separation** — `generate_reason` returns a short "Because you watched X" string. `_matched_attrs` returns topic/style/tone/creator context as separate pills for visual display.
8. **Video files on R2** — YouTube blocks data center IPs, so videos are hosted on Cloudflare R2 (`tl-substack-style-app` bucket, public URL). `download_videos.py` fetches from R2 instead of YouTube.
9. **Render deployment** — Blueprint-based deploy from `render.yaml`. Persistent disk at `/var/pixeltable` stores embedded Postgres + video files. Entrypoint script fixes pgdata permissions on redeploy.
10. **Resilience by default** — Twelve Labs rate-limits, 502s, and file-size limits all degrade gracefully to title similarity or empty results rather than 500s or hung frontends.

## Deployment

### Production URLs
- **Frontend**: https://substack-style-rec.vercel.app
- **Backend**: https://substack-rec-api-g2ui.onrender.com
- **R2 Videos**: https://pub-3d90ba141b2a453d9ada94f279c78419.r2.dev/

### Render Setup
1. Blueprint from `render.yaml` → creates web service (Starter, $7/mo) + disk (20 GB, $5/mo).
2. Set env vars: `TWELVELABS_API_KEY`, `CORS_ORIGINS`, `TWELVELABS_INDEX_ID`.
3. After deploy, Shell: `uv run download_videos.py --full && uv run setup_pixeltable.py --full`
4. Manual Deploy to restart server with populated DB.
5. If PostgreSQL lock errors after redeploy: `rm -f /var/pixeltable/pgdata/.s.PGSQL.5432.lock /var/pixeltable/pgdata/.s.PGSQL.5432 /var/pixeltable/pgdata/postmaster.pid`

### Cloudflare R2
- Bucket: `tl-substack-style-app` (25 video files, ~3.4 GB)
- Public URL enabled. Files have URL-safe names (special chars removed from originals).
- Upload via `npx wrangler r2 object put --remote` (< 300 MB) or `aws s3 cp --endpoint-url` (> 300 MB).

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
CORS_ORIGINS=http://localhost:3000,http://localhost:3002
PIXELTABLE_HOME=./data                            # Optional: scope Pixeltable to this repo
```

### Render (set in dashboard, not committed)
```
TWELVELABS_API_KEY=tlk_...
TWELVELABS_INDEX_ID=69c37b6708cd679f8afbd748
CORS_ORIGINS=https://substack-style-rec.vercel.app
PIXELTABLE_HOME=/var/pixeltable
```

See [`README.md`](./README.md#quick-start) for the full run order.

## Recent Changes (2026-04-22 → 2026-04-28)

- **Recommendation explainability**: Separated reason (short text) from matchedAttributes (pills). Topic overlap prioritized, creator context added ("New creator: X", "From your subscriptions").
- **Nav dropdowns**: Subscriptions (count + list + unsubscribe) and Watch History (thumbnails + reset all) added to navigation bar.
- **TL Search API integration**: Text search now calls Twelve Labs Search API directly, returning scene-level start/end timestamps and scene thumbnails. No Pixeltable scene detection needed.
- **Search UI overhaul**: Results show rank badge, scene time range, category pill next to title, and matched scene thumbnail. File upload search removed (not in PRD).
- **Video download from R2**: Replaced yt-dlp with direct R2 downloads. Removed yt-dlp dependency.
- **Render deployment**: Dockerfile moved to repo root, entrypoint fixes pgdata permissions. Blueprint-based deploy with persistent disk.
- **Console logging**: Browser DevTools shows recommendation scores for For You and Similar endpoints.
- **VideoPlayer startTime**: Supports `?t=` query param for scene-level deep linking from search results.

## Session 2026-05-08 → Open Issue: Render Initial-Populate OOM

### What landed (all in `main`)

Six PRs merged in this session, all summarized in their commit messages:

- **PR #6** Cache client-side API responses (5-min in-memory Map + inflight de-dup).
- **PR #7** Empty default subscriptions; bumped `localStorage` key to `curatorai-user-state-v2` so existing browsers reset.
- **PR #8** Live subscription badges in Up Next (client-side recompute of `source` / `contextTag` from `useUserState().isSubscribed`).
- **PR #9** Polish For You: recency-weighted scoring (max → weighted sum, weights `[0.5, 0.25, 0.125, 0.0625, 0.0625]`), cold-start clean cards (empty `reason`/`matchedAttributes`), hero loading spinner (drop `videos[0]` fallback), ref-scene sampling for `for-you` (`MAX_REF_SCENES_FOR_YOU = 6`).
- **PR #10** Summary + Chapters on watch page. New UDFs `summarize_video` / `chapters_for_video`, `Chapter` type, `forwardRef` + `useImperativeHandle` on `<VideoPlayer>` exposing `seekTo(t)`, click-to-seek chapter list under "About this video".
- **PR #11** Drop OpenCV scene-detect path; pull precomputed Marengo segment embeddings via `GET /indexes/{id}/indexed-assets/{vid}?embedding_option=visual` (`fetch_tl_segments` UDF). Flat `scenes` table with `Required[Array[(512,), Float]]` `visual_embedding` indexed via `add_embedding_index(string_embed=marengo)`.
- **PR #12** Pre-compute `summary` / `chapters` to `backend/summaries.json` (76 KB → 86 KB), UDFs prefer cache before falling back to `/analyze`.
- **PR #13** Cache `analyze_video` (topic/style/tone) in the same JSON. After this, `/analyze` is **never** called during a normal Render setup.
- Hotfixes on `main`: dedupe Up Next sidebar by `video.id` (mirrors VideoRow dedupe); remove "More Info" button from hero; wrap `.attr-pill` in `@layer components` so Tailwind v4 doesn't drop the rule; switch summary/chapters from deprecated `/summarize` (HTTP 410 since 2026-01-07) to `/analyze`.

### Open issue: Render initial populate keeps dying

Render auto-deployed everything from `main`. The deployed code is correct (`/api/videos` returns the new `summary` / `chapters` fields, recommendations work). The remaining problem is repopulating Pixeltable on Render's persistent disk so the columns aren't `null`:

- We expect `setup_pixeltable.py --full` to make zero `/analyze` calls thanks to the JSON cache.
- It does — only `/indexed-assets/...?embedding_option=visual` GETs (cheap) and `/embed-v2` POSTs for the title text embedding.
- Despite that, `setup_pixeltable.py` keeps dying mid-run on Render Starter (512 MB). Each restart progresses ~3–9 videos and then the Python process is gone (no traceback in the log → SIGKILL pattern, almost certainly the OOM-killer).
- Olivia Dean's video (`69c381d3fb98262c9024310c`) returns HTTP 400 from every TL endpoint (`/analyze`, `/indexed-assets`). Handled gracefully via try/except; that single video's row ends up with empty derived fields. Not the OOM cause.
- The deployed FastAPI process (`PID 44` in the previous container) is also using the same Pixeltable embedded Postgres on `/var/pixeltable/pgdata`. When setup runs as a separate process it tries to **start** another postmaster on the same socket → `FATAL: lock file already exists`. `kill 44` from inside the container returns `Operation not permitted` (capability drop).
- Workaround that works: trigger Render `Manual Deploy` or wait for a container swap. SSH into the **fresh** container and run setup before FastAPI's Pixeltable init grabs the lock. With `nohup` + `disown`, setup survives SSH disconnects but **not** container restarts.
- Best progress so far this session was 18/25 unique rows in the videos table; another restart is needed.

### How to resume next session

Render currently has a partially-populated Pixeltable. The simplest finish path:

1. SSH in (use SSH, not Web Shell — Web Shell drops constantly):
   ```sh
   ssh srv-d7o1sj77f7vs7384ad70@ssh.oregon.render.com
   ```
2. If the previous setup process is gone:
   ```sh
   cd /app
   ls /proc/*/cmdline 2>/dev/null | xargs -0 -I{} grep -l setup_pixeltable {} 2>/dev/null
   ```
   No output → safe to relaunch.
3. Restart setup (idempotent — skips already-inserted IDs by primary key):
   ```sh
   rm -f /var/pixeltable/pgdata/.s.PGSQL.5432.lock /var/pixeltable/pgdata/postmaster.pid
   nohup uv run setup_pixeltable.py --full > /var/pixeltable/setup.log 2>&1 &
   disown
   ```
4. Watch progress (does not need to stay attached):
   ```sh
   grep "Inserting videos" /var/pixeltable/setup.log | tail -3
   tail -10 /var/pixeltable/setup.log
   ```
5. After each death (logs stop advancing for >2 min, `kill -0 <pid>` says dead), repeat step 3. Each cycle adds another batch.
6. Final check (paste-safe one-liner):
   ```sh
   uv run python3 -c "import pixeltable as pxt, config; v = pxt.get_table(f'{config.APP_NAMESPACE}.videos'); rows = list(v.select(v.id).collect()); print('total:', len(rows), 'unique:', len(set(r['id'] for r in rows)))"
   ```
   Target: `total: 25 unique: 25`. Olivia Dean's row will be present but with empty `summary` / `chapters` / `tl_segments`.
7. Live verification from local:
   ```sh
   curl -s "https://substack-rec-api-g2ui.onrender.com/api/videos?limit=1" | python3 -m json.tool
   ```
   Look for non-null `summary` and a non-empty `chapters` array.

### Known landmines for next time

- Render Web Shell **disconnects too easily**. Use SSH (already configured with the user's `~/.ssh/id_rsa.pub`).
- Terminal-paste autoindent in this Render shell mangles multi-line commands and heredocs (`  EOF` is treated as content, not terminator). Use single-line commands or `base64 -d` round-trips for scripts.
- `videos.insert(batch, on_error="ignore")` does **not** dedupe by primary key the way we expected — re-running setup without `drop_dir` accumulates duplicate rows. Always `drop_dir` before a fresh population, never re-run setup mid-flight without it.
- Container restarts kill `nohup` processes too. Only SSH disconnects are survived.
- If the OOM keeps biting at the same batch, the long-term fix is either a bigger Render plan (Standard, 2 GB, ~$25/mo) or moving setup out of the request path (entrypoint script that runs before uvicorn — drafted but not yet shipped).

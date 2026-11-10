# HANDOFF.md — Substack TV-Style Recommendation Engine

> Last updated: 2026-11-10
>
> This is the one agent handoff for this repo. Start with "Current task". The session logs at the bottom are history.
> Other docs:
> - **Setup & quick start** → [`README.md`](./README.md)
> - **Agent guide** → [`AGENTS.md`](./AGENTS.md) (loaded by `CLAUDE.md`)
> - **Test report for the live database** → [`docs/PR18_UPGRADE_REVIEW.md`](./docs/PR18_UPGRADE_REVIEW.md)

---

## Current task: move the live app to Marengo 3.5

Branch `marengo-model-upgrade`. This section is for the person or agent with access to the Render service.

### What is done

- The backend uses Pixeltable 0.7.24 and twelvelabs 1.3.8.
- Pixeltable 0.7.24 adds `pxtf.twelvelabs.async_embed_asset` ([pixeltable/pixeltable#1907](https://github.com/pixeltable/pixeltable/pull/1907)). It runs a TwelveLabs async embedding task and returns one fused visual and audio vector for a whole clip of any length. The synchronous Marengo 3.5 call rejects audio and video over 30 seconds, and the scene clips average about 88 seconds.
- `backend/app.py` is the schema for a new install. Scene clips use `async_embed_asset`, and text and image queries use `embed`, both with `model_name="marengo3.5"`.
- `backend/app_existing_marengo35.py` is the schema for the live database. It is `app_existing.py` with the two named indexes, `title_marengo` and `scene_marengo`, switched to Marengo 3.5. Nothing else changes.
- `backend/upgrade_existing_marengo35.py` applies that schema to the live database. By default it only prints the plan. With `--apply` it drops the two indexes and builds them again with Marengo 3.5. It keeps every row, the Analyze tags, the scene cuts, and the scene clips. It refuses any other schema change. It sets Pixeltable's row buffer to 64, the value that worked on Render in June.

### What was tested, and what was not

These tests ran on a laptop, not on Render.

- A new install with 3 videos built with no errors. Search and recommendations work.
- The same 3 videos were loaded into the old code (Pixeltable 0.7.18, Marengo 3.0), and the two backends were compared request by request. The catalog, creators, style, and tone are the same. Recommendations take the same time, about 40 to 70 ms.
- A copy of the live schema was built with 1 video on Marengo 3.0. The upgrade script rebuilt its indexes with Marengo 3.5 in 33 seconds. The Analyze tags, scene cuts, and clip rows were the same before and after. Search, vector reuse, and title search work after the rebuild. A second run reports that there is nothing to do.
- The Docker image was built from the committed code with the repo's `Dockerfile` (Python 3.13.18, ffmpeg 7.1.5), on ARM Linux in a local VM. Inside it, the 15 backend tests pass. A new install loaded 3 videos with 0 errors. The server, started with `entrypoint.sh`, answered every endpoint, including text, image, and video search, the three recommendation endpoints, and the CORS check. The upgrade script ran the plan, `--apply`, and a rerun on a copy of the live schema with 1 video.
- The frontend production build (`npm run build`) passes, and the home, watch, search, and how-it-works pages work in a browser against the new backend.

These things were not tested.

- Nothing was run on the live server.
- The Docker image was not built for x86_64 Linux, which is what Render runs.
- The memory use of the rebuild on Render was not measured.
- The full set of 25 videos and 476 clips was not rebuilt anywhere.

### What changes for users

The local comparison found these differences.

- Search results come back in a different order on some queries, because the model changed. Where the right answer is clear, Marengo 3.5 did better. On 3 test queries, and on the image and audio uploads, Marengo 3.0 ranked the wrong video first.
- Scores are lower for text queries and closer together for video to video matches. The app does not show scores, so users only see the order.
- Search by uploaded video or audio takes about 1 to 2 minutes instead of about 15 to 25 seconds, because it runs as an async task.

### What happens when the pull request is merged

1. Render rebuilds and restarts the backend service, because `autoDeploy` is on for `main`. This takes about 3 to 5 minutes. Vercel rebuilds the frontend.
2. The backend starts with Pixeltable 0.7.24 and opens the live database on the persistent disk. Pixeltable may upgrade the format of the database metadata at this point. After that, the old code cannot open the database unless you restore a backup.
3. The live indexes still use Marengo 3.0, so search and recommendations still return Marengo 3.0 results. The frontend text already says Marengo 3.5.
4. The live site uses Marengo 3.5 only after someone runs the upgrade script on the server, in steps 4 to 8 below.

### Facts about the live server

- The backend is the Render web service `substack-rec-api` at https://substack-rec-api-g2ui.onrender.com. The frontend is at https://substack-style-rec.vercel.app.
- `PIXELTABLE_HOME` is `/var/pixeltable`, on a persistent disk. `/app` is wiped on every deploy.
- On 2026-10-27 the live database was a Pixeltable 0.6.x database with 25 videos and 476 scene clips. 111 of the clips had no vector. It uses the schema in `app_existing.py`, with indexes named `title_marengo` and `scene_marengo`. See `docs/PR18_UPGRADE_REVIEW.md`.
- In June, the 476 clip index build ran out of memory on the 2 GB instance. It worked on a 4 GB instance with the row buffer set to 64, and took about 8 minutes. See gotcha 1 under History.
- Changing the Render instance size changes the user that Postgres runs as, and the database stops. The fix is gotcha 2 under History.
- A Pixeltable job that is killed can leave database locks that block the live app. The fix is gotcha 4 under History.
- Render stops a process started over SSH when the session ends. Start long jobs with `setsid`.

### Steps for the agent

Stop and report back at every point marked STOP. Do not go past a STOP without approval from Alison or Pierre.

Never run these on the live server. They are for new installs and would delete or reload the live data.

- `uv run pxt schema update app.py substack_rec`
- `./run_setup_logged.sh` (with or without `--drop-dir`)
- `uv run load.py`
- `pxt.drop_dir`

Connect to the Render service over SSH (Render dashboard, then the service, then Connect, then SSH). Run every command from `/app`.

#### Step 1. Check the live database, before the merge

These commands only read.

```bash
cd /app
echo "$PIXELTABLE_HOME"                                   # expect /var/pixeltable
uv run python -c "import pixeltable; print(pixeltable.__version__)"
uv run pxt idxs                                           # look for title_marengo and scene_marengo
uv run pxt count substack_rec/videos                      # expect 25
uv run pxt count substack_rec/video_scenes                # expect 476
uv run migrate_existing.py --home /var/pixeltable         # dry run of the schema adoption
df -h /var/pixeltable
free -m
```

If the `pxt` command or `migrate_existing.py` does not exist, the server is still on code from before pull request #18. Report that.

STOP. Report the Pixeltable version, the index names, the counts, the full `migrate_existing.py` output, the free disk space, and the memory.

#### Step 2. Back up the database, before the merge

1. In the Render dashboard, open the service's disk and confirm that a snapshot from today exists. Write down its time.
2. Make a database dump while the app is running.

```bash
cd /app
PGBIN=$(uv run python -c "import os, pixeltable_pgserver; print(os.path.join(os.path.dirname(pixeltable_pgserver.__file__), 'pginstall', 'bin'))")
"$PGBIN/pg_dump" -h /var/pixeltable/pgdata -U postgres -d pixeltable -Fc -f /var/pixeltable/pre-marengo35.dump
ls -lh /var/pixeltable/pre-marengo35.dump
```

The dump holds the tables and the vectors. It does not hold the video clip files, so the disk snapshot is the full backup. Copy the dump off the Render disk if you can.

STOP. Report the snapshot time and the dump size.

#### Step 3. Merge the pull request and check the deploy

After Alison or Pierre approves, merge the pull request into `main`. Wait for the Render deploy to finish. The Render log shows "Connected to Pixeltable schema" when the service is up.

```bash
curl -s https://substack-rec-api-g2ui.onrender.com/health
curl -s "https://substack-rec-api-g2ui.onrender.com/api/search?q=branding" | head -c 400
```

Open https://substack-style-rec.vercel.app and check that the home page, a watch page, and search load.

STOP if the service does not come up. Report the Render log.

#### Step 4. Adopt the schema, only if step 1 showed it is needed

Skip this step if the dry run in step 1 printed "Catalog is up to date."

```bash
cd /app
uv run migrate_existing.py --home /var/pixeltable           # plan
uv run migrate_existing.py --home /var/pixeltable --apply   # only after the plan is approved
```

This changes metadata only. It does not touch rows or indexes.

#### Step 5. Dry run of the upgrade

```bash
cd /app
uv run upgrade_existing_marengo35.py --home /var/pixeltable
```

The output should list exactly two indexes that "will be REPLACED", `title_marengo` and `scene_marengo`, and end with "Dry run only".

STOP if it prints "Refusing" or anything else. Report the full output.

#### Step 6. Rebuild the indexes with Marengo 3.5

Agree on a time with Alison or Pierre first. Search and recommendations cannot use the scene index while it is rebuilt. The rebuild makes about 476 TwelveLabs async embedding tasks, which covers about 11.6 hours of video.

Memory comes first. The recommended way is to repeat what worked in June.

1. With approval, scale the service to the 4 GB instance.
2. Apply gotcha 2 under History, so that Postgres starts again.
3. Run the rebuild with the default row buffer of 64.

Running on 2 GB without resizing has not been tested, and the same build ran out of memory there in June.

Start the rebuild detached and follow its log.

```bash
cd /app
setsid bash -c 'cd /app && uv run upgrade_existing_marengo35.py --home /var/pixeltable --apply > /var/pixeltable/upgrade-marengo35.log 2>&1' < /dev/null &
tail -f /var/pixeltable/upgrade-marengo35.log
```

In a second SSH session, watch memory with `free -m` every minute or so.

- A clip that fails to embed does not stop the build. Pixeltable records the error on that clip and leaves its vector empty.
- If the job stops before it prints "Rebuilt title_marengo and scene_marengo", first clear any stale locks (gotcha 4 under History). Then run the same command again. The script continues from where it stopped.
- If the service runs out of memory and restarts, STOP and report.

When it finishes, the log ends with the number of videos, the number of clips, and the number of clips without a vector.

#### Step 7. Restart the web service

Restart the service from the Render dashboard, so the running app loads the new indexes. If you scaled to 4 GB in step 6, scale back to 2 GB now, and apply gotcha 2 again.

#### Step 8. Check the result

```bash
cd /app
uv run pxt idxs
# expect: scene_marengo ... async_embed_asset(video_segment, model_name='marengo3.5')
#         title_marengo ... embed(title, None, model_name='marengo3.5')
uv run upgrade_existing_marengo35.py --home /var/pixeltable   # expect "Nothing to do"
curl -s "https://substack-rec-api-g2ui.onrender.com/api/search?q=fade%20out%20ending%20pop%20song" | head -c 400
```

Then open https://substack-style-rec.vercel.app.

- Watch two or three videos, and check that the "similar videos" list fills in within a second or two.
- In the Render log, each recommendation request should show `[scene index] query=2 scene vectors (vector reuse)`.
- Try a text search and an image upload search.

STOP. Report the index lines, the clip counts (and how many have no vector, against 111 before), how long step 6 took, and the peak memory you saw.

### How to roll back

Restore the disk snapshot from step 2, then revert the merge commit on `main`. Do both. After step 3, the database metadata may be in the Pixeltable 0.7.24 format, and the old code cannot open it.

### Background

- Marengo 3.0 and Marengo 3.5 vectors are both 512 numbers long, but they are not compatible. An index must use one model for both the stored vectors and the queries. That is why the upgrade rebuilds the indexes.
- Pixeltable 0.7.24 also fixed scene detection ([pixeltable/pixeltable#1800](https://github.com/pixeltable/pixeltable/pull/1800)). A new install now gets one more clip at the end of each video, and some cut times move. The live database keeps its existing cuts and clips, because the upgrade script does not recompute them.
- The clips are cut with `video_splitter(mode="fast")`. On the local videos, a clip edge was at most 0.16 seconds from the detected cut. `mode="accurate"` would re-encode every clip, take about 27 times longer to split, and need the clips embedded again, so it was not used.
- `backend/functions.py` keeps a stub of the retired `embed_video_retry` UDF. A database built from an older `app.py` names it in its scene index, and Pixeltable must be able to import it to load and replace that index. The live database does not use it.

### Sources

- TwelveLabs migration guide for Marengo 3.0 to 3.5, with the sync and async limits: https://docs.twelvelabs.io/docs/get-started/migration-guides/marengo-3-0-to-3-5
- [pixeltable/pixeltable#1907](https://github.com/pixeltable/pixeltable/pull/1907) (PXT-1722) adds `async_embed()` and `async_embed_asset()`. Its description explains why `embed()` does not switch to the async API for long clips.
- [pixeltable/pixeltable#1732](https://github.com/pixeltable/pixeltable/pull/1732) (PXT-1553) adds Marengo 3.5 to the synchronous `embed()`, with the 30 second and 32 MB limits.
- [pixeltable/pixeltable#1902](https://github.com/pixeltable/pixeltable/pull/1902) (PXT-1234) makes the TwelveLabs UDFs wait until an uploaded asset is ready. This is why the app no longer needs its own retry UDF.
- [pixeltable/pixeltable#1800](https://github.com/pixeltable/pixeltable/pull/1800) (PXT-1380) is the scene detection fix described above.

---

## Project Overview

AI-powered video recommendation demo in the style of Substack TV. Uses Twelve Labs Marengo 3.5 embeddings + Pixeltable for semantic, explainable, cross-creator recommendations. The live server still uses Marengo 3.0 until the current task above is done.

**Goal**: Demonstrate TwelveLabs multimodal video understanding for ISV creator platforms (Substack, UScreen, Kajabi) with Netflix-style discovery.

## Architecture

```
Next.js 16 frontend (localhost:3000)
       |  NEXT_PUBLIC_API_BASE
       v
FastAPI backend (localhost:8000)
       |
       v
Pixeltable 0.7.24
  ├── creators table (10 creators)
  ├── videos table (25 indexed videos + pxt.Video + Analyze API attrs)
  ├── video_scenes view (scene_detect_histogram + video_splitter mode=fast)
  ├── scene embedding index (one Marengo 3.5 vector per scene clip, async_embed_asset)
  └── title embedding index (text fallback)
       |
       v
Twelve Labs API (Embed v2 + Analyze)
```

The live database names the two indexes `scene_marengo` and `title_marengo`. A new install from `app.py` leaves them unnamed.

### Data flow

- **Default** — Browser → Next.js `/api/*` routes → Twelve Labs (fallback when no backend).
- **With backend** — Set `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`. Browser → FastAPI → Pixeltable → Twelve Labs.

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, hls.js |
| Backend | FastAPI + Pixeltable 0.7.24 + `uv` package management |
| Embeddings | Twelve Labs Marengo 3.5 (512-dim). Scene clips use the async embedding API; text and image queries use the synchronous API. Title index as fallback. |
| Attribute Extraction | Twelve Labs Analyze API with Pegasus 1.5 (topic / style / tone) |
| Scene Detection | Pixeltable `scene_detect_histogram` + `video_splitter(mode='fast')` |
| Video Player | hls.js with CloudFront HLS URLs from Twelve Labs |
| Storage | Local Pixeltable Postgres (`PIXELTABLE_HOME`) |

## Implementation Status

### Complete
- Pixeltable schema: creators + videos + `video_scenes` view with scene-level Marengo 3.5 embeddings.
- Scene detection via `scene_detect_histogram` + stream-copy `video_splitter(mode='fast')` — no re-encoding.
- Analyze API computed columns: topic, style, tone run automatically on INSERT.
- All endpoints: `/api/videos`, `/api/creators`, `/api/recommendations/{for-you,similar,creator-catalog}`, `/api/search` (GET text + POST multimodal).
- 70 / 30 subscription / discovery split with max-2-per-creator diversity.
- Explainable recommendations (`generate_reason`).
- Cold start fallback (latest from subscriptions + discovery).
- Multimodal search (image / video / audio file upload → cross-modal scene matching).
- Resilience: title-similarity fallback on API failures, frontend decoupled loading so one failing endpoint never blocks the page.
- Backend on Render, frontend on Vercel.

### Open
- Move the live database to Marengo 3.5 (the current task above).
- Session-based live personalization (re-rank within a session based on in-session clicks).

## Content

25 longform videos indexed in Twelve Labs, drawn from a curated set of 30 across 11 creators and 4 categories. Full breakdown in [`README.md`](./README.md#content) and the raw list in [`scripts/curate_videos.csv`](./scripts/curate_videos.csv).

- **Twelve Labs index**: `69c37b6708cd679f8afbd748` (`substack-style-rec`). The index was created with Marengo 3.0 and Pegasus 1.2. The app reads only video metadata, HLS URLs, and asset IDs from it, so the index's own models do not affect the app's embeddings.
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
| `download_videos.py` | Fetch MP4 files from YouTube (or the R2 mirror with `--r2`) |
| `pxt schema update app.py substack_rec` | Create the tables, view, and indexes for a new install |
| `load.py` | Insert the videos; Analyze, scene detection, and embeddings run on insert |
| `run_setup_logged.sh` | `pxt.drop_dir` reset, schema update, and load, with logging to `backend/logs/` |
| `migrate_existing.py` | Adopt an existing 0.6.x database with `app_existing.py`, metadata only |
| `upgrade_existing_marengo35.py` | Rebuild the existing database's two indexes with Marengo 3.5 |
| `main.py` | Start FastAPI on `:8000` |

## Key Decisions

1. **Dual data source** — Frontend works against Next.js `/api/*` (TL direct) or FastAPI + Pixeltable, toggled by `NEXT_PUBLIC_API_BASE`. Keeps the demo runnable without the backend.
2. **Scene-level retrieval** — `video_scenes` is the primary index; the title index is the fallback when scene embedding or the Embed API fails. All rec + search paths use both helpers in `backend/routers/videos.py`.
3. **`user_metadata` as source of truth** — Creator / category / upload date live in Twelve Labs, not in local JSON. `scripts/update_tl_metadata.py` writes; runtime only reads.
4. **Analyze as computed columns** — Topic / style / tone run automatically on INSERT, so attribute-based recommendation reasons are always available.
5. **Diversity + hybrid discovery** — 70 / 30 subscription / discovery split with max 2 videos per creator. Prevents the classic filter bubble without abandoning subscribed creators.
6. **Local-first Pixeltable** — `PIXELTABLE_HOME=./data` under `backend/` so other Pixeltable projects on the same machine stay untouched. `pxt.drop_dir(substack_rec)` is the safe reset — never delete `~/.pixeltable`. The `pxt` CLI runs in a daemon that does not read `.env` files, so export `PIXELTABLE_HOME` and `PXT_PORT` before any manual `pxt` command (`set -a; source .env.local; set +a`). `run_setup_logged.sh` does this itself.
7. **Resilience by default** — Twelve Labs rate-limits, 502s, and file-size limits all degrade gracefully to title similarity or empty results rather than 500s or hung frontends.
8. **One vector per scene clip** — Scene clips are embedded with `async_embed_asset`, which returns one fused vector per clip. `async_embed()` returns many vectors per clip, and the synchronous `embed()` rejects clips over 30 seconds.

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
PXT_PORT=22189                                    # pxt CLI daemon port for this project
```

See [`README.md`](./README.md#quick-start) for the full run order.

---

## History

These session logs are kept as a record. Facts in them may be out of date. The "Current task" section above wins where they disagree.

### Session Log — 2026-06-09 (production recovery: "CORS error" was actually a dead Postgres)

**Symptom:** Live app played video but all recommendation calls (`/api/recommendations/{similar,for-you}`) failed in the browser with "blocked by CORS policy: No Access-Control-Allow-Origin". Video still played because HLS comes straight from CloudFront, not the backend.

**Root cause:** Yesterday's scale-down 4GB→2GB raced two postmasters; the survivor left a stale `.s.PGSQL.5432.lock` (pointing at dead PID 38) on the persistent disk. A later postmaster hit `FATAL: lock file ... already exists` and refused to start, so **Postgres stayed dead**. The FastAPI app's `/health` still returned 200 (no DB), but every DB-backed endpoint returned **HTTP 500 — and 500 error responses carry no CORS headers**, which the browser reports as a CORS failure. So "CORS error" was a misleading symptom of a 500, not an actual CORS misconfig (CORS_ORIGINS was correct the whole time).

**Fix (non-destructive — no file deletion needed):** `kill -TERM 1` to restart the container. Postgres 16 detects the stale lock's PID is dead and **auto-clears it on startup** → DB came up clean (`database system is ready to accept connections`). After that, `similar` returned video-to-video `Nordic homestead 0.7958` (true Strategy-1 scene match, not the 0.295 text fallback). This is a lighter fix than 2026-06-08 gotcha #2's `rm` + `chown` — try a plain restart FIRST; only delete the stale lock/socket if a process still holds the old PID.

**Also corrected:** the public hostname is `substack-rec-api-g2ui.onrender.com` (`g2ui`), not `q2ui` as previously written here. Wasted time hitting the wrong host (`x-render-routing: no-server` 404). Always read `RENDER_EXTERNAL_HOSTNAME` from `/proc/1/environ` to confirm. The Vercel frontend bundle was already pointing at the correct `g2ui` host.

**Perf fix — `/similar` was 85s, now ~1s (matched Pierre's live deploy).** Root cause: the merged PR #14 (`updates` branch) recommendation path re-embedded the reference video's scene clips via the Twelve Labs Embed API **on every request** (`_get_ref_scene_segments` + `_scene_similarity(video=seg_path)`) — 2 clips × ~40s = 85s. Pierre's *live* site runs his `main` branch, which is the **stored-vector** approach (the `8a71d51 "use stored Marengo scene embeddings"` method, originally written here, then lost in a rollback to `archive/main-pre-rollback`). PR #14 was Pierre's `updates` branch — NOT the fast `main` he actually deploys, so we inherited the slow path. Fix: `_get_ref_scene_vectors` reads the precomputed vectors from the `scene_marengo` index via `video_segment.embedding(idx="scene_marengo")` and queries with `_scene_similarity(vector=vec)` — no query-time upload. Same true video-to-video quality (scores 0.78–0.91), ~80× faster. `_scene_similarity` already passed `**sim_kwargs` through, so only `recommendations.py` changed. how-it-works copy updated to say "cached scene vectors / reusing vectors Marengo computed at setup" instead of "sending clips to Marengo." **Verified live** via Render logs: `[scene index] query=2 scene vectors (vector reuse)` on every call, no fallback. Shipped in `ba800ca`.

**Deploy self-heal — `entrypoint.sh` now clears the stale Postgres socket lock on boot** (`c22ff57`). This is the permanent fix for the recurring "every redeploy kills Postgres" problem (gotcha #2 below). The deploy that shipped it self-healed with no manual restart. Note: **every push to `main` triggers a full Render redeploy** (`autoDeploy: true`) — that's now safe, the container fixes itself, but expect a ~3–5 min build + swap window.

---

### Session Log — 2026-06-08 (PR #14 merge + production deploy of video-to-video)

**Goal of the day:** Merge Pierre's PR #14 (real video-to-video recommendations via scene embeddings, replacing the silent title-only fallback) and get it working live on Render + Vercel.

**Outcome: ✅ video-to-video recommendations are LIVE and verified.**
Example (live `/api/recommendations/similar` on the homestead video):
`Nordic homestead 0.796`, `underground home 0.745` — content-matched via Marengo scene embeddings, not title text.

#### What was done
1. **PR #14 merged.** It was a cross-repo PR from `pierrebrunelle:updates` → `mrnkim:main`. Resolved the one conflict (`src/lib/api.ts`: kept BOTH the `withCache` wrapper and `dedupeById`/`dedupeRecs` — dedupe runs inside each cache callback). Fast-forwarded `main` to `230e00e`, closed PR #14 with a merge comment (cross-repo PRs don't auto-close).
2. **Added `curl` to the Docker image** (`6c8d00e`) — `download_videos.py --r2` shells out to `curl`, which the slim base image lacked.
3. **Rebuilt the scene pipeline on Render** (the deployed DB had the embedding index missing AND old `fps=2` scenes):
   - Dropped old `video_scenes` view + `scenes` column, re-downloaded 25 videos (`--r2 --full`), recomputed `scene_detect_histogram(fps=1, threshold=0.9, min_scene_len=900)` → **476 scenes** (vs old 1707), rebuilt the `scene_marengo` embedding index.

#### Deployment facts (Render)
- Service: **`substack-rec-api`**, SSH handle from the Render dashboard (Service → Connect → SSH; form `srv-<service-id>@ssh.oregon.render.com`), public URL **`https://substack-rec-api-g2ui.onrender.com`** (it's `g2ui`, **not** `q2ui` — confirm via `tr '\0' '\n' < /proc/1/environ | grep RENDER_EXTERNAL_HOSTNAME`). The Vercel bundle already points here correctly.
- Frontend (Vercel): **`https://substack-style-rec.vercel.app`**, `CORS_ORIGINS=https://substack-style-rec.vercel.app` (correct)
- `PIXELTABLE_HOME=/var/pixeltable` is the **persistent disk** (survives redeploys: pgdata + scene media). `/app` is **ephemeral** (wiped on every redeploy/restart — including `/app/video_files` and `/tmp`).
- **Currently on Standard (2GB)** — was bumped to Pro (4GB) only for the one-time index build, then scaled back down (serving fits in 2GB). Re-bump to 4GB if you ever rebuild the embedding index.

#### ⚠️ Hard-won gotchas (read before touching the Render box again)
1. **Embedding-index build OOMs on 2GB.** Pixeltable decodes scene segments into RAM before embedding. Default `ExprEvalNode.MAX_BUFFERED_ROWS=2048` loads all 476 at once → >2GB → Render kills the container (shows as silent death, `oom_kill=0` because it's Render's own memory limit, not the Linux OOM killer). Fix used: bumped to **4GB** and monkeypatched `MAX_BUFFERED_ROWS=64` → built in 454s, peak 3.5GB. `MAX_BUFFERED_ROWS=4` *stalls* the pipeline; 64 is the working/safe value at 4GB. **This memory fix is NOT in code yet — see follow-ups.**
   (2026-11-10 update: `upgrade_existing_marengo35.py` now sets this to 64 by default for the Marengo 3.5 index rebuild.)
2. **Changing the Render instance type breaks Postgres.** Going 2GB→4GB changed the uid Postgres runs as (data was owned by uid 1000, new instance ran pg as `pgserver` uid 1001) → `pg_ctl` fails with `could not open lock file ... Permission denied` → whole DB down → app 500s → frontend shows CORS errors (no headers on failed responses). **Fix:** `chown -R pgserver:pgserver /var/pixeltable/pgdata` + remove stale `.s.PGSQL.5432` socket and `.s.PGSQL.5432.lock`, then restart the app (`kill -TERM 1` → Render restarts the container). Scaling **back down to 2GB will likely re-break this** (ownership flips again).
   **(2026-06-09) The stale-socket-lock half of this is now fixed permanently in `Dockerfile`'s `entrypoint.sh`** — on every boot it clears `.s.PGSQL.5432.lock` + socket unless a live `postgres` process holds the recorded PID. Verified: the deploy that shipped it self-healed (Postgres `ready` at 02:08, no `FATAL: lock file already exists`, no manual `kill -TERM 1`). The *ownership* failure mode (uid flip on instance-type change) is NOT auto-fixed — still needs the manual `chown` above if you resize the instance.
3. **Long jobs over SSH must use `setsid`** — Render kills SSH-spawned processes when the session drops, *unless* fully detached (`setsid bash -c "..." </dev/null &`).
4. **Killed Pixeltable processes leave stale Postgres locks** (`idle in transaction`) that block ALL subsequent DB ops, including the live app. Clean with `pg_terminate_backend(pid)` on `state like '%transaction%'`.
5. `scene_detect_histogram` on all 25 videos (~11.6h of footage) takes **~102 min single-threaded** on this box. `add_embedding_index` over 476 scenes takes ~8 min at `MAX_BUFFERED_ROWS=64`.

#### Follow-ups / open
- **Code-ify the memory fix:** make `setup_pixeltable.py`'s `add_embedding_index` honor a low `MAX_BUFFERED_ROWS` (env-configurable) so a future re-setup doesn't OOM on 2GB. Currently a manual monkeypatch only.
  - 2026-11-10 update: `setup_pixeltable.py` no longer exists. For the Marengo 3.5 index rebuild, `upgrade_existing_marengo35.py --max-buffered-rows` (default 64) applies this fix. A new install with `load.py` still uses Pixeltable's default.

#### Done (was open)
- ✅ Scaled Render back to 2GB (Standard). Serving runs fine.
- ✅ Frontend renders recommendations end-to-end — confirmed via live Render logs: every `/similar` and `/for-you` logs `[scene index] query=N scene vectors (vector reuse)` (Strategy 1), no text/title fallback, scores 0.79–0.86, ~1s.
- ✅ Stale-socket-lock on deploy fixed permanently in `entrypoint.sh` (see gotcha #2). Every push to `main` auto-redeploys and now self-heals Postgres without manual `kill -TERM 1`.

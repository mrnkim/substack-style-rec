# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint (flat config, eslint.config.mjs)
npm start            # Serve production build
```

No test framework is configured yet.

## Architecture

Substack TV-style video recommendation engine demo. Next.js 16 frontend that fetches video data from Twelve Labs API (25 videos, HLS streaming). Will connect to a FastAPI + PixelTable backend for embedding-based recommendations.

```
Pages → src/lib/api.ts → /api/* routes → src/lib/twelve-labs.ts → Twelve Labs API
                          (future: swap to PixelTable FastAPI URL)
```

### Frontend (this repo)

- **Next.js 16** App Router with React 19, TypeScript, Tailwind CSS v4
- Path alias: `@/*` maps to `./src/*`
- All pages in `src/app/` (dynamic routes: `[id]`), all client components
- API routes in `src/app/api/` proxy Twelve Labs API
- Shared components in `src/components/`
- Data layer + types in `src/lib/`

### Key layers

- **`src/lib/twelve-labs.ts`** — Server-side TL API client; fetches videos from index, maps `user_metadata` to `Video` type
- **`src/lib/api.ts`** — Client-side fetch helpers (`getVideos`, `getVideo`, `getCreators`, `getCreator`). Change `API_BASE` to swap to PixelTable
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

### API Routes

| Route | Source |
|---|---|
| `GET /api/videos` | `src/app/api/videos/route.ts` |
| `GET /api/videos/[id]` | `src/app/api/videos/[id]/route.ts` |
| `GET /api/creators` | `src/app/api/creators/route.ts` |
| `GET /api/creators/[id]` | `src/app/api/creators/[id]/route.ts` |

### Design system

- Dark theme with TwelveLabs brand green (`#00DC82`) accent on warm charcoal background
- Fonts: Instrument Serif (display, `--font-display`), Geist (body, `--font-geist-sans`), Geist Mono (`--font-geist-mono`)
- CSS uses `noise` class on body for texture overlay

### Environment variables

```
TWELVELABS_API_KEY=tlk_...    # Required, in .env.local
TWELVELABS_INDEX_ID=...       # Required, in .env.local
```

### Scripts

- `scripts/update_tl_metadata.py` — Uploads creator/category metadata from CSV to TL `user_metadata`
- `scripts/download_and_collect.py` — YouTube download + metadata collection (one-time)
- `scripts/curate_videos.csv` — Curated video list with YouTube IDs

## Current state

Phase 1 complete: 25 real videos from Twelve Labs index with HLS playback, CloudFront thumbnails, 10 creators. Video attributes (topic/style/tone) not yet extracted. Next: PixelTable integration for embedding-based recommendations. See `HANDOFF.md` for full status.

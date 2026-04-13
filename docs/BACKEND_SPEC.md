# Backend Specification for PixelTable Team

> Substack TV-Style Recommendation Engine — Backend Requirements

## Overview

This document specifies the backend API and data pipeline for the PixelTable team to implement.

**Reference architecture**: [Creator Discovery App](https://github.com/pierrebrunelle/pixeltable/tree/sample-app/creator-discovery-app/docs/sample-apps/creator-discovery-app) — same FastAPI + PixelTable + Twelve Labs pattern

## Architecture

```
Next.js Frontend
       │
       │ REST API (JSON)
       ▼
┌──────────────────────────────────────────┐
│  FastAPI (thin read layer)               │
│  • /api/videos, /api/creators            │
│  • /api/recommendations/*                │
│  • /api/search                           │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  PixelTable (unified data backend)       │
│  • Tables: videos, creators              │
│  • Computed columns: embeddings,         │
│    attributes, segments                  │
│  • Embedding indexes: Marengo 3.0        │
│  • .similarity() for recommendations     │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  Twelve Labs API                         │
│  • Marengo 3.0: multimodal embeddings    │
│  • Analyze API: attribute extraction     │
└──────────────────────────────────────────┘
```

## PixelTable Schema

### `creators` Table

| Column | Type | Computed | Description |
|---|---|---|---|
| `id` | `pxt.Required[pxt.String]` | No | Unique creator ID (primary key) |
| `name` | `pxt.String` | No | Creator display name |
| `avatar_url` | `pxt.String` | No | Profile image URL |
| `description` | `pxt.String` | No | Creator bio |

### `videos` Table

| Column | Type | Computed | Description |
|---|---|---|---|
| `id` | `pxt.Required[pxt.String]` | No | Twelve Labs video_id (primary key) |
| `title` | `pxt.String` | No | Video title |
| `creator_id` | `pxt.String` | No | FK to creators |
| `category` | `pxt.String` | No | interview / commentary / creative / educational |
| `duration` | `pxt.Int` | No | Duration in seconds |
| `thumbnail_url` | `pxt.String` | No | Thumbnail URL |
| `hls_url` | `pxt.String` | No | HLS streaming URL |
| `upload_date` | `pxt.String` | No | ISO date string |
| `video` | `pxt.Video` | No | Local video file reference (for segment splitting) |
| `raw_attributes` | Computed | Yes | JSON from Analyze API |
| `topic` | Computed | Yes | Free-form topic tags, e.g. `["AI", "robotics"]` — extracted from `raw_attributes` |
| `style` | Computed | Yes | Enum: `interview \| documentary \| essay \| tutorial \| conversation \| analysis \| performance \| explainer` |
| `tone` | Computed | Yes | Enum: `serious \| casual \| playful \| contemplative \| energetic \| analytical` |

### Embedding Indexes

**Title index** (on `videos` table) — used by the recommendation engine to find similar videos based on watch history titles:

```python
videos.add_embedding_index('title', string_embed=marengo, idx_name='title_marengo')
```

### `video_scenes` View (primary search index)

Uses Pixeltable's built-in `scene_detect_histogram` to find natural scene boundaries, then `video_splitter` with `mode='fast'` (stream copy, no ffmpeg re-encoding) to split at those points. Each scene segment is embedded with Marengo 3.0 for cross-modal search.

```python
videos.add_computed_column(
    scenes=videos.video.scene_detect_histogram(fps=2, threshold=0.8, min_scene_len=120),
)
video_scenes = pxt.create_view(
    'substack_rec.video_scenes',
    videos,
    iterator=video_splitter(
        video=videos.video,
        segment_times=videos.scenes[1:].start_time,
        mode='fast',
    ),
)
video_scenes.add_embedding_index('video_segment', embedding=marengo, idx_name='scene_marengo')
```

All search queries (text and file uploads) go through `video_scenes` for content-based matching. Results are deduplicated back to unique videos (keeping the highest-scoring scene per video).

## API Endpoints

### GET `/api/videos`

List all videos (paginated).

**Query params:**
- `page` (int, default 1)
- `limit` (int, default 20)
- `category` (string, optional) — filter by category
- `creator_id` (string, optional) — filter by creator

**Response:**
```json
{
  "data": [
    {
      "id": "tl_video_abc123",
      "title": "The Future of AI in Media",
      "creator": {
        "id": "creator_01",
        "name": "Tech Interviews Weekly",
        "avatar_url": "https://..."
      },
      "category": "interview",
      "duration": 1847,
      "thumbnail_url": "https://...",
      "upload_date": "2025-11-15",
      "attributes": {
        "topic": ["AI", "media", "technology"],
        "style": "interview",
        "tone": "serious"
      }
    }
  ],
  "page": 1,
  "total": 28,
  "total_pages": 2
}
```

### GET `/api/videos/:id`

Single video detail.

**Response:** Single video object (same schema as above)

### GET `/api/creators`

List all creators.

**Response:**
```json
{
  "data": [
    {
      "id": "creator_01",
      "name": "Tech Interviews Weekly",
      "avatar_url": "https://...",
      "description": "Weekly deep-dive interviews with tech leaders",
      "video_count": 4
    }
  ]
}
```

### GET `/api/creators/:id`

Creator detail + video list.

**Response:**
```json
{
  "creator": { "id": "...", "name": "...", "..." },
  "videos": [ ... ],
  "total_videos": 4
}
```

### POST `/api/recommendations/for-you`

**Core endpoint** — generates "For You" recommendations.

**Request:**
```json
{
  "subscriptions": ["creator_01", "creator_03"],
  "watch_history": ["video_abc", "video_def", "video_ghi"],
  "limit": 10
}
```

**Logic:**

**Cold start fallback** (when `watch_history` is empty):
1. If `subscriptions` is non-empty → return latest videos from subscribed creators, padded with recent videos from other creators for discovery
2. If `subscriptions` is also empty → return editorially curated or most recent videos across all creators
3. Apply creator diversity (max 2 per creator) and return with `source: "subscription"` or `"discovery"` accordingly
4. Set `score: null` and `reason: "New to you"` (no similarity basis)

**Standard flow** (when `watch_history` is non-empty):
1. Query `.similarity(string=title)` using titles of recently watched videos as seeds (last 5) — prefers `video_scenes.video_segment` for content-based matching, falls back to `videos.title` if scenes are unavailable
2. Deduplicate chunk results to unique videos (keep highest-scoring segment per video)
3. Exclude already-watched videos
4. **70/30 balancing**:
   - 70% from subscribed creators (top similarity matches)
   - 30% from unsubscribed creators (discovery)
5. **Creator diversity**: max 2 per creator
6. Best score wins when the same video matches multiple watch history entries

**Response:**
```json
{
  "recommendations": [
    {
      "video": { "..." },
      "score": 0.87,
      "reason": "Similar interview style to 'The Future of AI in Media'",
      "matched_attributes": ["in-depth interview", "technology", "serious tone"],
      "source": "subscription"
    }
  ]
}
```

### POST `/api/recommendations/similar`

Recommend videos similar to a specific video (for watch page sidebar).

**Request:**
```json
{
  "video_id": "video_abc",
  "watch_history": ["video_abc", "video_def"],
  "limit": 6
}
```

**Logic:**
1. Query `.similarity(string=title)` using the reference video's title — prefers `video_scenes`, falls back to `videos.title`
2. Deduplicate chunk results to unique videos
3. Exclude already-watched videos and the current video
4. Creator diversity: max 2 per creator

**Response:** Same schema as for-you endpoint

### POST `/api/recommendations/creator-catalog`

Sort a creator's catalog by relevance to user interests (not recency).

**Request:**
```json
{
  "creator_id": "creator_01",
  "watch_history": ["video_abc", "video_def"],
  "limit": 20
}
```

**Logic:**
1. Filter to only this creator's videos
2. Sort by relevance to `watch_history` embeddings (interest-based, not chronological)
3. Include watched/unwatched status

**Response:**
```json
{
  "creator": { "..." },
  "recommended": [ ... ],
  "popular": [ ... ]
}
```

### GET `/api/search?q=`

Text-based semantic video search. Queries the `video_scenes` view for content-based matching (falls back to title embeddings if scenes are unavailable).

**Query params:**
- `q` (string, required) — search query
- `creator_id` (string, optional) — scope search to a single creator's catalog
- `limit` (int, default 10)

**Logic:**
1. `video_scenes.video_segment.similarity(string=q)` — searches actual video content
2. Deduplicate results to unique videos (keep highest-scoring segment per video)
3. If `creator_id` provided, filter to only that creator's videos
4. Rank by similarity score

### POST `/api/search`

Multimodal search — upload an image, video clip, or audio file to find matching videos via Marengo 3.0 cross-modal embeddings.

**Form fields:**
- `file` (file, optional) — image, video, or audio file
- `q` (string, optional) — text query (used as fallback if file fails)
- `creator_id` (string, optional) — scope to a single creator
- `limit` (int, default 10)

**Supported modalities:** image (jpg/png/webp/gif), video (mp4/webm/mov), audio (mp3/m4a/wav)

**Logic:**
1. Detect file modality from MIME type or extension
2. `video_scenes.video_segment.similarity(image=path)` (or `video=`, `audio=`)
3. Deduplicate results to unique videos
4. Rank by similarity score

**Response (both GET and POST):**
```json
{
  "query": "interviews about technology policy",
  "modality": "text",
  "results": [
    {
      "video": { "..." },
      "score": 0.82
    }
  ]
}
```

### POST `/api/videos/upload`

Self-serve video upload. Pixeltable auto-runs scene detection, embedding, and attribute extraction on the uploaded file.

**Form fields:**
- `file` (file, required) — mp4/webm/mov video file
- `title` (string, required) — video title
- `category` (string, default "interview") — interview / commentary / creative / educational

**Limits:** `MAX_UPLOAD_SIZE_MB` (default 100), `MAX_UPLOAD_DURATION_SEC` (default 300)

**Response:**
```json
{
  "id": "upload_a1b2c3d4e5f6",
  "title": "My Video",
  "status": "processing"
}
```

## Recommendation Explanation Generation

Logic for generating natural-language recommendation reasons:

1. For each recommended video, identify which video in `watch_history` had the highest similarity score — this is the **source video**
2. Compare `attributes` (topic, style, tone) between source and recommended videos
3. Extract 2-3 overlapping attributes
4. Generate from templates, prefixed with source video context:
   - Source context: "Because you watched '{source_video_title}'"
   - Topic match: "Also covers {topic}"
   - Style match: "Similar {style} format"
   - Tone match: "Matching {tone} tone"
   - Creator context: "From a creator you subscribe to" / "Discover a new creator"

**Attribute enums** (Analyze API should pick from these fixed options):

- `style`: interview, documentary, essay, tutorial, conversation, analysis, performance, explainer
- `tone`: serious, casual, playful, contemplative, energetic, analytical
- `topic`: free-form string array (no fixed options)

**Example outputs:**
- "Similar in-depth interview style, also covers AI and technology"
- "Matching serious analytical tone — discover a new creator"
- "From a creator you subscribe to — explores related political themes"

## Data Ingestion Pipeline

Computed column pipeline that should auto-execute on video INSERT:

```
INSERT video
  → Generate Marengo 3.0 embedding (computed column)
  → Extract topic/style/tone via Analyze API (computed column)
    - topic: free-form string array
    - style: pick from enum (interview|documentary|essay|tutorial|conversation|analysis|performance|explainer)
    - tone: pick from enum (serious|casual|playful|contemplative|energetic|analytical)
  → Auto-update embedding index
```

**Note**: Video download and Twelve Labs indexing are handled by separate pre-processing scripts.

### Analyze API Prompt

Use this prompt in the Twelve Labs Analyze API computed column to extract attributes. The prompt constrains style and tone to fixed enums so recommendation matching is deterministic.

```
Analyze this video and extract the following attributes. Return valid JSON only.

{
  "topic": ["topic1", "topic2", ...],   // 2-5 key topics, free-form strings
  "style": "one_of_enum",               // pick ONE from the list below
  "tone": "one_of_enum"                 // pick ONE from the list below
}

style options (pick exactly one):
- "interview": one-on-one or panel conversation with a guest
- "documentary": narrative-driven visual storytelling, observational
- "essay": opinion-driven, first-person argument or reflection
- "tutorial": step-by-step instructional or how-to content
- "conversation": casual multi-person discussion, podcast-style
- "analysis": data-driven or research-backed breakdown of a topic
- "performance": music, comedy, art, or live performance
- "explainer": educational breakdown of a concept using visuals or animation

tone options (pick exactly one):
- "serious": formal, weighty subject matter, measured delivery
- "casual": relaxed, informal, conversational energy
- "playful": lighthearted, humorous, fun
- "contemplative": reflective, slow-paced, thought-provoking
- "energetic": fast-paced, enthusiastic, high energy
- "analytical": methodical, logic-driven, data-focused
```

### Credentials Required from TwelveLabs Team

The PixelTable team needs these values (provided by us) to configure the computed columns:

| Variable | Description | Provided by |
|---|---|---|
| `TWELVELABS_API_KEY` | API key for Embed + Analyze calls | TwelveLabs team |
| `TWELVELABS_INDEX_ID` | Index ID where videos are indexed (created after upload) | TwelveLabs team |

## Setup Script Pattern

Example `setup_pixeltable.py` (following [Pixeltable + Twelve Labs docs](https://docs.pixeltable.com/howto/providers/working-with-twelvelabs.md)):

```python
import pixeltable as pxt
from pixeltable.functions.twelvelabs import embed
from pixeltable.functions.video import video_splitter

marengo = embed.using(model_name='marengo3.0')

pxt.create_dir('substack_rec', if_exists='ignore')

videos = pxt.create_table(
    'substack_rec.videos',
    {
        'id': pxt.Required[pxt.String],
        'title': pxt.String,
        'creator_id': pxt.String,
        'category': pxt.String,
        'duration': pxt.Int,
        'thumbnail_url': pxt.String,
        'hls_url': pxt.String,
        'upload_date': pxt.String,
        'video': pxt.Video,
    },
    primary_key=['id'],
    if_exists='ignore',
)

# Title embedding index (used by recommendations engine)
videos.add_embedding_index('title', string_embed=marengo, idx_name='title_marengo')

# Attribute extraction via Analyze API (computed columns)
videos.add_computed_column(raw_attributes=analyze_video(videos.id))
videos.add_computed_column(topic=videos.raw_attributes['topic'])
videos.add_computed_column(style=videos.raw_attributes['style'])
videos.add_computed_column(tone=videos.raw_attributes['tone'])

# Scene detection + scene-based view for content search
videos.add_computed_column(
    scenes=videos.video.scene_detect_histogram(fps=2, threshold=0.8, min_scene_len=120),
)
video_scenes = pxt.create_view(
    'substack_rec.video_scenes',
    videos,
    iterator=video_splitter(
        video=videos.video,
        segment_times=videos.scenes[1:].start_time,
        mode='fast',
    ),
)
video_scenes.add_embedding_index('video_segment', embedding=marengo, idx_name='scene_marengo')
```

## CORS Configuration

Required for Next.js (Vercel) → FastAPI communication:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variables

```
TWELVELABS_API_KEY=tlk_xxx
TWELVELABS_INDEX_ID=xxx
PIXELTABLE_HOME=./data     # or cloud config
```

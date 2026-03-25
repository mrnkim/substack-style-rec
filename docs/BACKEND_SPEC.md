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
| `id` | `pxt.String` | No | Unique creator ID |
| `name` | `pxt.String` | No | Creator display name |
| `avatar_url` | `pxt.String` | No | Profile image URL |
| `description` | `pxt.String` | No | Creator bio |

### `videos` Table

| Column | Type | Computed | Description |
|---|---|---|---|
| `id` | `pxt.String` | No | Twelve Labs video_id |
| `title` | `pxt.String` | No | Video title |
| `creator_id` | `pxt.String` | No | FK to creators |
| `category` | `pxt.String` | No | interview / commentary / creative / educational |
| `duration` | `pxt.Int` | No | Duration in seconds |
| `thumbnail_url` | `pxt.String` | No | Thumbnail URL |
| `upload_date` | `pxt.String` | No | ISO date string |
| `video` | `pxt.Video` | No | Video file reference |
| `embedding` | Computed | Yes | Marengo 3.0 embedding via Twelve Labs |
| `topic` | Computed | Yes | Free-form topic tags (Analyze API), e.g. `["AI", "robotics"]` |
| `style` | Computed | Yes | Enum: `interview \| documentary \| essay \| tutorial \| conversation \| analysis \| performance \| explainer` |
| `tone` | Computed | Yes | Enum: `serious \| casual \| playful \| contemplative \| energetic \| analytical` |

### Embedding Index

```python
videos.add_embedding_index(
    column='video',          # or 'title' for text-based
    embedding=marengo_embed, # Twelve Labs Marengo 3.0
)
```

### Views (Optional Enhancement)

```python
# Segment view for finer-grained similarity
segments_view = pxt.create_view(
    'video_segments',
    videos,
    iterator=pxtf.video.video_splitter(videos.video, duration=30)  # 30s segments
)
segments_view.add_embedding_index('video_segment', embedding=marengo_embed)
```

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
1. Query `.similarity()` using embeddings of videos in `watch_history`
2. Exclude already-watched videos
3. **70/30 balancing**:
   - 70% from subscribed creators (top similarity matches)
   - 30% from unsubscribed creators (discovery)
4. **Creator diversity**: max 2 per creator
5. Optional: slight boost for recent uploads from subscribed creators

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
1. Query `.similarity()` using the embedding of `video_id`
2. Exclude already-watched videos
3. Creator diversity: max 2 per creator

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

Semantic video search.

**Query params:**
- `q` (string, required) — search query
- `limit` (int, default 10)

**Logic:**
1. PixelTable `.similarity(string=q)` — text-to-video cross-modal search
2. Rank by similarity score

**Response:**
```json
{
  "query": "interviews about technology policy",
  "results": [
    {
      "video": { "..." },
      "score": 0.82
    }
  ]
}
```

## Recommendation Explanation Generation

Logic for generating natural-language recommendation reasons:

1. Compare `attributes` (topic, style, tone) between source and recommended videos
2. Extract 2-3 overlapping attributes
3. Generate from templates:
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

Example `setup_pixeltable.py` (following Creator Discovery App pattern):

```python
import pixeltable as pxt

# Idempotent setup
pxt.create_dir('substack_rec', if_exists='ignore')

creators = pxt.create_table(
    'substack_rec.creators',
    {
        'id': pxt.String,
        'name': pxt.String,
        'avatar_url': pxt.String,
        'description': pxt.String,
    },
    if_exists='ignore'
)

videos = pxt.create_table(
    'substack_rec.videos',
    {
        'id': pxt.String,
        'title': pxt.String,
        'creator_id': pxt.String,
        'category': pxt.String,
        'duration': pxt.Int,
        'thumbnail_url': pxt.String,
        'upload_date': pxt.String,
        'video': pxt.Video,
    },
    if_exists='ignore'
)

# Add Marengo 3.0 embedding index
videos.add_embedding_index('title', embedding=marengo_embed)
videos.add_embedding_index('video', embedding=marengo_embed)
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

## Questions for PixelTable Team

1. Can PixelTable call Twelve Labs Marengo 3.0 embeddings directly as a computed column? Or should embeddings be pre-computed and stored?
2. Can `.similarity()` results be filtered by conditions (e.g., `creator_id IN [...]`)?
3. Should recommendation explanation generation happen in PixelTable computed columns or in the FastAPI layer?
4. Deployment: Where will the PixelTable server be hosted? (Render, Railway, EC2, etc.)
5. Can Analyze API attribute extraction be integrated as a PixelTable UDF?

# Product Requirements Document (PRD): Substack TV-Style Recommendation Engine Demo

## 🎯 Objective

Enable ISV creator platforms (UScreen, Substack, Kajabi) to power Netflix-style video discovery and personalized recommendations using TwelveLabs' multimodal video understanding. Demonstrate how semantic embeddings, cross-creator search, and explainable recommendations surface the right longform content at the right moment—without manual tagging.

## 😢 Problem Statement

- Creator platforms struggle to build effective video recommendation engines that go beyond view counts and metadata, limiting content discovery and subscriber engagement with deep creator catalogs.
- Substack TV launched with a "For You" row but [explicitly calls out "improved discovery"](https://on.substack.com/p/introducing-the-substack-tv-app-now) as a future enhancement, leaving back catalogs underutilized and cross-creator discovery shallow.
- Unlike text-based content, video requires understanding semantic meaning, narrative pacing, tone, and thematic connections—capabilities that traditional recommendation engines lack.
- Creators with 50+ videos in their libraries see recent uploads dominate discovery while high-quality evergreen content gets buried by recency bias, reducing content ROI.

## 🗣️ Use Cases

- **"For You" Row Intelligence**: Power Substack TV's recommendation feed by surfacing personalized videos from subscriptions and semantically similar content from new creators, balancing familiarity with discovery.
- **Deep Catalog Surfacing**: Help subscribers find relevant older videos from a creator's 50+ video library based on watch history and interests, not just chronological order.
- **Cross-Creator Discovery**: Bridge content communities by recommending thematically similar videos across different creators (e.g., "Because you watched this political interview, you might enjoy this author discussing political themes in fiction").
- **Explainable Recommendations**: Show subscribers *why* each video was suggested with transparent attributes like "Similar interview style," "In-depth political analysis," or "Literary exploration."

## 🎨 User Interaction and Design

- **Personalized "For You" Homepage**: Recommendation row that adapts based on simulated watch history, with clear "Because you watched..." context and creator diversity (max 2 per creator).
- **Intelligent Creator Pages**: Creator catalogs organized by relevance to user interests, not just recency, with "Recommended from this creator" row surfacing older high-quality content.
- **Cross-Subscription Exploration**: Dedicated section for videos from creators the user doesn't subscribe to, framed as "Explore beyond your subscriptions" with semantic matching.
- **Recommendation Explanations**: Hover or click interactions revealing 2-3 key attributes explaining why each video was suggested, building trust and transparency.

## 🤔 Requirements

| **Requirement** | **Importance** | **Description** |
| --- | --- | --- |
| Semantic video understanding with Marengo embeddings | HIGH | Capture longform content essence (interview tone, topic depth, narrative pacing, creator energy) using multimodal embeddings for accurate similarity matching |
| Cross-creator semantic search | HIGH | Enable "Because you watched X on [Creator A], you might like Y on [Creator B]" recommendations by finding thematic overlaps across creator silos |
| Explainable recommendations with Analyze API | HIGH | Generate transparent 2-3 attribute explanations per video (e.g., "In-depth interview," "Political analysis") to build subscriber trust |
| Hybrid subscription + discovery recommendation engine | HIGH | Balance subscription-first content (70%) with TwelveLabs-powered discovery (30%), blending recency with semantic relevance |
| Deep catalog intelligence | MEDIUM | Surface relevant older videos from creators with 50+ video libraries based on semantic matching, not recency bias |
| Session-based refinement | MEDIUM | Adapt recommendations in real-time as users watch more content during demo session, demonstrating live personalization |

## 🧫 Appendix

### 1 - Technical Differentiation

- Multimodal embeddings capture visual, audio, speech, and on-screen text with temporal coherence, enabling robust thematic matching beyond traditional collaborative filtering or metadata-based recommendations.
- Semantic search across full video corpora allows precise content retrieval based on narrative style, topic depth, and creator tone—not just tags or titles.
- Analyze API generates structured explanations for recommendations, improving transparency and subscriber trust in discovery features.

### 2 - Substack TV Context & Market Opportunity

- Substack TV launched with a "For You" row that surfaces videos from subscriptions plus recommended content, but their roadmap explicitly calls out "improved discovery" as a future enhancement.
- Substack positions as the "home for longform" with "thought-provoking videos" that deserve "extended viewing"—this isn't TikTok-style surface recommendations, but deep semantic understanding of interview styles, narrative arcs, and thematic connections.
- The wedge opportunity: TwelveLabs powers the intelligent recommendation engine that makes Substack TV's "For You" row truly personalized, helping creators' back catalogs get discovered and keeping subscribers engaged beyond immediate subscriptions.

### 3 - Demo Content Strategy

- **Curated Video Mix (25-30 videos)**: Interview/Conversation (40%), Commentary/Analysis (30%), Creative/Performance (20%), Educational/How-To (10%)—mirrors Substack's actual content distribution.
- **Why this mix?** Demonstrates cross-category discovery (e.g., "If you liked this political interview, you might enjoy this author discussing political themes in fiction").
- **Licensing**: Use Creative Commons or properly licensed longform creator content with metadata: creator name, title, category, upload date.

### 4 - Architecture Workflows

**Workflow 1: Video Ingestion & Indexing**

- Prepare 25-30 longform creator videos with metadata (creator name, title, category, upload date)
- Create TwelveLabs index with Marengo-3.0, generating multimodal embeddings (visual + audio + text)
- Store: video_id, embedding, metadata
- Optional: Use Analyze API to extract topic, style, pacing attributes for explanation generation
- **Key Decision**: Pre-compute embeddings and attributes during setup for fast recommendation generation during demo

```markdown
┌─────────────────────────────────────────────────────────────┐
│  CONTENT PREPARATION                                        │
│  • 25-30 longform creator videos (Creative Commons/licensed)│
│  • Metadata: creator name, title, category, upload date     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  TWELVELABS INDEXING                                        │
│  • Create TwelveLabs index with Marengo-3.0                 │
│  • Generate multimodal embeddings (visual + audio + text)   │
│  • Store: video_id, embedding, metadata                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ATTRIBUTE EXTRACTION (Optional Enhancement)                │
│  • Use Analyze API to extract: topic, style, pacing         │
│  • Store alongside embeddings for explanation generation    │
└─────────────────────────────────────────────────────────────┘
```

**Workflow 2: "For You" Row Recommendation Generation**

1. User watches Video A or views simulated watch history
2. Query TwelveLabs Embed API with Video A
3. Retrieve top 10-15 semantically similar videos
4. Apply filters: remove already-watched videos, ensure creator diversity (max 2 per creator), balance subscription vs. discovery (70/30 split), optional boost for recent uploads from subscriptions
5. Select top 6 recommendations
6. Generate explanations by matching extracted attributes between source and recommended videos
7. Render UI with "For You" row: video thumbnails + titles, "Because you watched..." context, hover/click for detailed explanation
- **Key Decision**: Balance between subscription-first (Substack's current model) and discovery (TwelveLabs' value-add); demo should toggle between modes

```markdown
┌─────────────────────────────────────────────────────────────┐
│  USER INTERACTION                                           │
│  User watches Video A (or views simulated watch history)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  RECOMMENDATION ENGINE                                      │
│  1. Query TwelveLabs Embed API with Video A                 │
│  2. Retrieve top 10-15 semantically similar videos          │
│  3. Apply filters:                                          │
│     • Remove already-watched videos                         │
│     • Ensure creator diversity (max 2 per creator)          │
│     • Balance subscription vs. discovery (70/30 split)      │
│     • Optional: boost recent uploads from subscriptions     │
│  4. Select top 6 recommendations                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  EXPLANATION GENERATION                                     │
│  • Match extracted attributes between source & recommended  │
│  • Generate natural language: "Similar interview style"     │
│  • Include creator name and video title                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  UI RENDER                                                  │
│  Display "For You" row with:                                │
│  • Video thumbnails + titles                                │
│  • "Because you watched..." context                         │
│  • Hover/click for detailed explanation                     │
└─────────────────────────────────────────────────────────────┘
```

**Workflow 3: Creator Catalog Deep-Dive**

- User navigates to specific Creator Page (e.g., "Political Commentary Creator" with 50+ videos)
- Query TwelveLabs: "Show me videos from this creator most similar to user's watch history"
- OR: Natural language query within creator catalog - "interviews about technology policy" → semantic search
- Sort results by relevance (not just recency)
- Render Creator page: "Recommended from this creator" row (personalized), "Popular episodes" row (view count fallback), optional thematic collections ("Their best interviews")
- **Key Decision**: Demonstrates TwelveLabs' value for creators with deep back catalogs—older, high-quality content gets surfaced intelligently instead of buried by recency bias

```markdown
┌─────────────────────────────────────────────────────────────┐
│  USER INTERACTION                                           │
│  User navigates to specific Creator Page (e.g., "Political  │
│  Commentary Creator" with 50+ videos)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  INTELLIGENT CATALOG ORGANIZATION                           │
│  • Query TwelveLabs: "Show me videos from this creator      │
│    most similar to user's watch history"                    │
│  • OR: Natural language query - "interviews about           │
│    technology policy" → semantic search within creator      │
│  • Sort results by relevance (not just recency)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  UI RENDER                                                  │
│  Creator page shows:                                        │
│  • "Recommended from this creator" row (personalized)       │
│  • "Popular episodes" row (view count fallback)             │
│  • Optional: Thematic collections ("Their best interviews") │
└─────────────────────────────────────────────────────────────┘
```
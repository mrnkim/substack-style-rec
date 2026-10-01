---
title: "Building Long-Form Video Discovery with TwelveLabs and Pixeltable"
search_title: "Build Long-Form Video Discovery with TwelveLabs & Pixeltable"
category: "Partnerships"
byline: "Alison Hill, TBD (TwelveLabs)"
subtitle: "Developers can build content-based discovery for long-form video by pairing TwelveLabs Marengo and Pegasus with Pixeltable, the multimodal backend that stores that context with the catalog and serves it to users."
meta_description: "Build long-form video discovery and search with TwelveLabs Marengo and Pegasus, kept in sync with the catalog and served from Pixeltable, a multimodal backend."
status: "DRAFT 1. TODO notes are in HTML comments. Step 3 waits for the PR #2 serving code."
---

[Code on GitHub](https://github.com/mrnkim/substack-style-rec)

## Introduction

Creator platforms now host large catalogs of long-form video, from interviews and documentaries to video essays and lectures. Discovery on most of them still depends on view counts, metadata, and upload dates, so recent uploads take the top rows and strong older videos drop out of view.

Discovery across creators stays shallow too, because two videos about the same idea rarely share a title or a tag. Substack TV is a recent example: its app launched in January with a "For You" row, and it lists [search and improved discovery](https://on.substack.com/p/introducing-the-substack-tv-app-now) as what's coming next.

Search and discovery beyond metadata are difficult to build. Titles and tags are already structured fields in a database, and ranking on them takes a single query.

Ranking on video content requires two capabilities.

The first is understanding what happens in every scene of every video, and this is where [TwelveLabs](https://www.twelvelabs.io/) comes in. [Marengo](https://www.twelvelabs.io/marengo) creates embeddings for video, audio, images, and text in one shared space, so a scene can be compared with a text query, an image, or another video. [Pegasus](https://www.twelvelabs.io/pegasus) generates structured attributes for each video through the [Analyze API](https://www.twelvelabs.io/product/analyze).

The second is keeping that understanding synced with the catalog for fast lookup, in a way that can be surfaced to users. Pixeltable covers that half. In a production application, the model output has to be computed for every scene, kept current as videos and models change, and served on every page load without a new model call. Every new feature touches all of that infrastructure: to build anything, you have to build everything. With [Pixeltable](https://www.pixeltable.com/), an open source multimodal backend, you keep the TwelveLabs output synced with the catalog, compute it on insert, and serve it to users from one application.

Together, these two tools can power more effective long-form discovery through four features that rank videos by content instead of by title or tag:

- **"For You" Row Intelligence:** Recommendations built from the scenes a viewer has watched, mixing creators they follow with creators they haven't found yet.
- **Deep Catalog Surfacing:** A creator's back catalog ranked by relevance to each viewer, so strong older videos come back into view.
- **Cross-Creator Discovery:** Similar videos from other creators when the content matches, even if the titles and tags don't.
- **Explainable Recommendations:** A short reason with each recommendation that names what the two videos share, such as topic, style, or tone.

These features follow patterns that large streaming services already use, such as personalized rows and "Because you watched" recommendations. What differs from one catalog to the next is the tuning: the mix of subscribed and new creators, the scene length, and which attributes to explain. With TwelveLabs and Pixeltable, a team can build each feature, tune it on its own videos, and change it without rebuilding the stack.

This tutorial walks through CuratorAI, a working demo of all four features. By the end, you'll know how the application turns each new video into scene vectors and attributes on insert, and how it serves recommendations from them in about a second.

[embed](https://www.youtube.com/embed/TODO) <!-- TODO: record the demo video (required: 90% of TwelveLabs posts) -->

Try the [live demo](https://substack-style-rec.vercel.app): watch two or three videos, then go back to the home page to see the "For You" row update.

### Why TwelveLabs for Long-Form Video

CuratorAI uses two TwelveLabs models, Marengo 3.0 and Pegasus 1.5 at the time of writing, and the [TwelveLabs video index](https://docs.twelvelabs.io/docs/concepts/indexes) that holds the videos:

- **Marengo:** Creates embeddings from video, audio, images, and text in one shared space. A scene clip, a written phrase, a photograph, and an audio sample can all be compared directly, which lets one index serve both recommendations and search.
- **Pegasus:** A video-to-text model that analyzes multiple modalities and can return structured JSON. It accepts videos up to two hours long, so one Analyze request covers a full episode.
- **The TwelveLabs video index:** Stores the full videos with their HLS streams, thumbnails, and custom metadata. CuratorAI streams playback from it and reads each video's creator, category, and upload date from it during loading. Search and recommendations don't query it: they run on Pixeltable's embedding indexes.

### Why Pixeltable for the Production App

[Pixeltable](https://github.com/pixeltable/pixeltable) is a multimodal backend. One app holds the whole backend: storage, the AI steps, search, and the API. You write it once, and the same app runs on a laptop and in production.

The alternatives have you stand up and connect each of those pieces first. One option is an app backend like [Supabase](https://supabase.com/) or [Convex](https://www.convex.dev/), with the AI processing built separately. The other is an assembled stack of [Postgres](https://www.postgresql.org/), object storage, a vector database such as [Pinecone](https://www.pinecone.io/), job scripts for the model calls, and an API server.

In that kind of stack, each new feature touches every system. With Pixeltable, a new feature is one addition to one backend: the AI steps you define run on every video the application inserts, and on the videos already stored when you add a step.

## Prerequisites

- A TwelveLabs API key from the [TwelveLabs Playground](https://playground.twelvelabs.io/).
- A TwelveLabs video index that contains your videos and their metadata. <!-- TODO(blocker): load.py reads one specific index (69c37b67...). Other accounts get 403. The upload script is not in the repo. Add an upload step before publication. -->
- Python 3.11 or later, the [uv](https://docs.astral.sh/uv/) package manager, and [ffmpeg](https://ffmpeg.org/) for video processing.
- [Node.js](https://nodejs.org/) 18 or later for the [Next.js](https://nextjs.org/) frontend.

Put your key and index ID in `backend/.env.local`, then install the backend, create the tables, and load three quick-start videos:

```bash
cd backend
uv sync
uv run download_videos.py
uv run pxt schema update app.py substack_rec
uv run load.py
```


## Architecture Overview

![Figure 1: CuratorAI architecture](assets/architecture.png) <!-- TODO: diagram from serving:src/components/architecture-diagram.tsx, plus the FastAPIRouter routes and the HLS path -->

*Figure 1: TwelveLabs provides the video understanding and the playback, while Pixeltable stores that context with the catalog and serves it to the frontend.*

CuratorAI has three parts: a Next.js frontend, a backend built on Pixeltable, and the TwelveLabs models and video index. The frontend renders the pages and keeps each viewer's subscriptions and watch history in the browser.

The backend holds the Pixeltable tables and the API. Each video is streamed to the browser directly from the TwelveLabs video index over HLS, so the backend never serves video files.

Every video moves through four steps:

1. **Store:** `load.py` inserts one row for each video, with its title, creator, category, HLS URL, and a reference to its video file.
2. **Compute on insert:** Pegasus returns the topic, style, and tone. Scene detection finds the cuts, the view splits the video into one clip for each scene, and Marengo embeds each clip.
3. **Answer queries:** a search embeds the query with Marengo and compares it with the stored scene vectors. A recommendation is answered from vectors that were stored at insert.
4. **Rank and explain:** application code balances creators, limits each creator to two recommendations, and assembles the "Because you watched" explanation.

This split also decides when the application calls TwelveLabs: at insert, each video gets one Analyze call, one Marengo embedding for its title, and one for each scene. Each search makes one Marengo call for the query, and a recommendation makes no TwelveLabs call at all.

Each kind of data is stored in one place:

| Data | Where it lives |
|---|---|
| Full videos, HLS streams, and thumbnails | The TwelveLabs video index |
| Video rows, Analyze results, and scene cut times | Pixeltable tables |
| Scene clips | Pixeltable's media store |
| Scene and title vectors (512 dimensions) | Embedding indexes in Pixeltable |
| Subscriptions and watch history | The viewer's browser |

### Why Scenes Are the Unit of Discovery

A long-form video usually covers many subjects, and a 40-minute interview can move from the guest's childhood to the business of streaming to a song they wrote last year.

A title, or a single embedding for the whole video, blurs those subjects together, so CuratorAI embeds each scene instead.

Marengo places each scene clip in the same multimodal vector space as text, images, and audio. As a result, one scene index can answer a text search, an image upload, a video clip, or an audio sample.

The 25 demo videos hold about 11.6 hours of footage, split into 476 scenes. <!-- TODO(verify): 476 comes from HANDOFF.md only; count with pxt count on substack_rec/video_scenes -->

## Step 1: Declare the Backend in app.py

The complete schema is defined in `backend/app.py`. Each class is a table, a type annotation is a stored column, and an assignment is a computed column that runs on insert.

Here is the `Videos` table, trimmed to the columns this tutorial explains:

```python
marengo = pxtf.twelvelabs.embed.using(model_name="marengo3.0")
TableModel = pxt.model_base()

class Videos(TableModel, name="videos"):
    id = pxt.Column(type=pxt.String, primary_key=True)
    title: pxt.String | None
    creator_id: pxt.String | None
    video: pxt.Video | None
    raw_attributes = analyze_video(id)
    topic = raw_attributes.topic
    style = raw_attributes.style
    tone = raw_attributes.tone
    scenes = video.scene_detect_histogram(fps=1, threshold=0.9, min_scene_len=900)
    __indexes__ = [pxt.EmbeddingIndex(title, string_embed=marengo)]
```

`raw_attributes` calls the Analyze API once for each new video. `topic`, `style`, and `tone` read fields from that result, and `scenes` stores the scene boundaries, while the title index is the text fallback for search.

`analyze_video` is a short user-defined function that calls the Analyze API. It sends the video's asset ID from the TwelveLabs video index to Pegasus, so the video isn't uploaded a second time:

```python
@pxt.udf(is_deterministic=False)
async def analyze_video(video_id: str) -> VideoAttributes:
    ...
    payload = {
        "model_name": "pegasus1.5",
        "video": {"type": "asset_id", "asset_id": asset_id},
        "prompt": config.ANALYZE_PROMPT,
    }
```

The prompt asks Pegasus for a list of topics, one of eight styles, and one of six tones. Here is part of it, which limits each answer to a fixed set of options:

```text
style options (pick exactly one):
- "interview": one-on-one or panel conversation with a guest
- "documentary": narrative-driven visual storytelling, observational
- "explainer": educational breakdown of a concept using visuals or animation

tone options (pick exactly one):
- "serious": formal, weighty subject matter, measured delivery
- "contemplative": reflective, slow-paced, thought-provoking
```

Fixed options keep Pegasus's attributes consistent across the whole catalog, and the explanations in Step 4 depend on that consistency.

The function's return type is a `TypedDict`, and Pixeltable uses that type definition, so `raw_attributes.topic` becomes a typed column instead of untyped JSON.

The scene view splits each video at its scene boundaries and indexes each clip:

```python
class VideoScenes(
    TableModel,
    name="video_scenes",
    base=Videos,
    iterator=pxtf.video.video_splitter(
        video=Videos.video, segment_times=Videos.scenes[1:].start_time, mode="fast"
    ),
):
    __indexes__ = [
        pxt.EmbeddingIndex(
            video_segment,
            embedding=embed_video_retry,
            string_embed=marengo,
            image_embed=marengo,
            audio_embed=marengo,
        )
    ]
```

Each row of the view is one scene clip, which is stored in Pixeltable's media store. `mode="fast"` copies the original stream without re-encoding, so each split falls on the nearest keyframe.

The index embeds every clip with Marengo when the row is inserted. `embed_video_retry` is a small wrapper that retries while TwelveLabs finishes processing an uploaded clip. Text, image, and audio queries use the same model through `marengo`.

Preview the schema changes, then create the tables, view, and indexes from the command line:

```bash
uv run pxt schema diff app.py substack_rec
uv run pxt schema update app.py substack_rec
```

[`pxt schema diff`](https://docs.pixeltable.com/overview/how-it-works) is read-only: it lists each change and marks it as safe, destructive, or unsupported, and `pxt schema update` applies nothing destructive unless you pass `--allow-destructive`.

## Step 2: Load and Explore the Tables in Python

The CLI creates and changes the tables, while ordinary Python code loads and queries them. `load.py` binds the classes to the `substack_rec` directory, then inserts rows in small batches:

```python
TableModel.bind_all(config.APP_NAMESPACE)
...
status = Videos.insert(batch, on_error="ignore")
```

Each insert runs the full chain for every new video: the Analyze call, scene detection, the scene split, and one Marengo embedding for each clip.

With `on_error="ignore"`, a failed step is recorded on its row, and the rest of the batch is still inserted. <!-- TODO: true for the scene embeds today. analyze_video returns default values on failure, so Analyze failures are not recorded. Fix the UDF in the PR. -->

The same tables are available in a notebook or a script. This text search is the same similarity query the API runs:

```python
import pixeltable as pxt

scenes = pxt.get_table("substack_rec.video_scenes")
sim = scenes.video_segment.similarity(string="why pop songs fade out")
scenes.order_by(sim, asc=False).limit(5).select(scenes.title, score=sim).collect()
```

<!-- TODO(verify): run this against the quick-start database -->

The [earlier TwelveLabs and Pixeltable tutorial](https://www.twelvelabs.io/blog/twelve-labs-and-pixeltable) built its tables with `pxt.create_table`, `add_computed_column`, and `add_embedding_index`. That form suits a notebook, where you explore one step at a time.

For an application, `app.py` and the CLI keep the whole schema in one file that you can review, diff, and apply. The CLI also covers the work after launch:

- `pxt errors` lists every row where a computed column failed, with the error message.
- `pxt recompute --errors-only` recomputes only the failed rows, along with the columns that depend on them.
- `pxt history` lists a table's versions, and `pxt revert` undoes the last operation.

## Step 3: Serve the Context to Users

<!-- TODO(blocked): this section waits for the PR #2 serving code. Write it from the merged code. Planned content:
  - One FastAPIRouter.add_query_route over a @pxt.query, for scene search.
  - File search with uploadfile_inputs.
  - The OpenAPI docs at /docs.
  - `uv run pxt service run app.py substack_rec` (local).
  - A screenshot of /docs. -->

The frontend asks for data on every page: the catalog, search results, and three kinds of recommendations. CuratorAI serves the parts that are table queries through Pixeltable's [`FastAPIRouter`](https://docs.pixeltable.com/howto/deployment/serving).

The ranking logic stays in plain Python on the same [FastAPI](https://fastapi.tiangolo.com/) app, because it isn't a single table query. It merges results from several watched videos, balances creators, and handles new viewers who have no history yet.

This part of the "For You" ranking fills 70% of the row from subscribed creators and 30% from new ones:

```python
n_sub = max(1, int(body.limit * 0.7))
n_disc = body.limit - n_sub
final_sub, final_disc = sub[:n_sub], disc[:n_disc]
```

This rule is ordinary product logic, so it belongs in ordinary code, while the similarity queries that feed it run in Pixeltable.

## Step 4: Build the Four Discovery Features

Each feature combines a semantic signal from TwelveLabs with a similarity query that runs inside Pixeltable.

### "For You" Row Intelligence

The home row starts from the five most recently watched videos. For each one, the application reads up to two of its stored scene vectors and queries the scene index with them:

```python
# simplified from backend/routers/recommendations.py
rows = (
    scenes_t.where(scenes_t.id == video_id)
    .select(vec=scenes_t.video_segment.embedding())
    .collect()
)
sim = scenes_t.video_segment.similarity(vector=rows[0]["vec"])
```

Marengo computed these vectors when each video was inserted, so the query makes no TwelveLabs call.

An earlier version of the application re-embedded the watched video's clips on every request, and a similar-videos call took about 85 seconds. Reusing the stored vectors brought it to about one second.

The ranking code from Step 3 then balances creators, and no creator gets more than two recommendations. The row changes as you watch, because each watched video becomes another source for the query.

### Deep Catalog Surfacing

A creator page runs the same scene query, filtered by `creator_id`. Its "Recommended from this creator" row ranks the back catalog by how close each video is to what you watched, not by upload date.

### Cross-Creator Discovery

The Up Next list on the watch page searches with the current video's stored scene vectors across the whole catalog. The two-per-creator limit prevents a single channel from dominating the list.

<!-- TODO: add one real Up Next result from the live demo, with scores, captured on the day of publication -->

### Explainable Recommendations

Each recommendation carries a short explanation built from the Pegasus attributes of both videos. A typical line reads: "Because you watched 'How to legislate AI' · Similar interview format · Matching serious tone."

<!-- TODO(verify): capture the exact line from the live demo; the code joins the first part with an em dash -->

A template builds the explanation, not a language model, so it adds no delay and says only what the stored attributes support.

### Search with Any Query Type

The search page accepts text, an image, a video clip, or an audio file as the query. Query video files must be under 36 MB for the [Embed API](https://www.twelvelabs.io/product/embed), so the search page accepts files up to 35 MB. <!-- TODO(verify) the 36 MB limit against the TwelveLabs Embed API docs; source today is a code comment in config.py --> Every query type reaches the same scene index through a different similarity argument: `similarity(string=...)`, `similarity(image=...)`, `similarity(video=...)`, or `similarity(audio=...)`.

For example, a text search for "music culture" returns Vox Earworm videos about smooth jazz, Stravinsky, and song fade-outs, although none of their titles contains either word. Marengo matches the meaning of the query to the content of the scenes. <!-- TODO(verify) on the live demo on the day of publication; observed 2026-09-30 -->

Search and the four features follow one pattern. TwelveLabs turns each scene and each query into a vector in one shared space, and Pixeltable stores those vectors with the catalog and answers the similarity query. Only the source of the query changes: a watch history, a creator, the current video, or the user's own input.

## Best Practices

- **Reuse stored vectors:** when the query is already in your catalog, read its vector with `.embedding()` and pass it to `similarity(vector=...)`, which removes a model call from every request.
- **Embed scenes, not full videos:** the application stores one Marengo vector for each clip, so the clip boundaries decide what each vector represents. Scene-length clips keep each vector focused on one subject.
- **Tune scene detection to your content:** CuratorAI uses `fps=1`, `threshold=0.9`, and `min_scene_len=900`. A higher threshold gives fewer scenes, so there are fewer clips to embed. Check the scene count on a few videos before you embed a full catalog.
- **Preview every schema change:** run `pxt schema diff` before `pxt schema update`, and keep destructive changes behind `--allow-destructive`.
- **Add context as a new column:** a new attribute, such as pacing, is one more computed column that calls the Analyze API. When you add it, it runs on every stored video, because Analyze reads each video from the TwelveLabs video index.
- **Rerun only what failed:** use `pxt errors` and `pxt recompute --errors-only` instead of running the whole catalog again. <!-- needs the analyze_video fix -->
- **Respect rate limits:** the custom embed function declares `resource_pool="request-rate:twelvelabs"`, so Pixeltable paces its calls to the TwelveLabs API.


## What This Approach Makes Possible

Content-based discovery no longer has to be a large investment made up front. A team can try all four features on its own catalog and see whether older videos and new creators start to surface.

Marengo finds the scenes that titles miss, Pegasus gives each video attributes that a recommendation can cite, and Pixeltable keeps both next to the catalog and serves them.

Discovery is not a one-time build. New videos arrive every day and need the same scene embeddings and attributes as the rest of the catalog. TwelveLabs keeps releasing better models, so stored vectors and attributes eventually need to be recomputed. The people building the product also think of new signals to rank on. A team might decide that pacing matters, so that a viewer who likes slow, reflective interviews sees more of them.

Every one of those changes costs engineering time and compute, so its scope matters. With Pixeltable, each new video gets the same steps on insert. A model or feature change is an edit to `app.py` and a schema update: `pxt schema diff` shows what will change before anything runs, and results already computed stay in place until you choose to rerun them.

The same backend can do more than this demo shows. A route that takes an upload could store a new video, run the Analyze call and the scene embeddings, and return the new context to the frontend, for many users at once.

Because the whole backend is one file plus a CLI that reports its results, a coding agent can build and change it too. Pixeltable is the backend agents build with.

## Resources

- [CuratorAI source code](https://github.com/mrnkim/substack-style-rec): the complete application, including the backend schema, the loading script, and the frontend.
- [CuratorAI live demo](https://substack-style-rec.vercel.app): the four features on 25 long-form videos from 10 creators.
- [Marengo](https://docs.twelvelabs.io/docs/concepts/models/marengo): the TwelveLabs embedding model for video, text, image, and audio.
- [Pegasus](https://docs.twelvelabs.io/docs/concepts/models/pegasus): the TwelveLabs video language model behind the Analyze API.
- [Analyze videos](https://docs.twelvelabs.io/v1.3/docs/guides/analyze-videos): the guide to prompts and structured output.
- [Create embeddings](https://docs.twelvelabs.io/docs/guides/create-embeddings): the Embed API guide for video, image, audio, and text embeddings.
- [Working with TwelveLabs in Pixeltable](https://docs.pixeltable.com/howto/providers/working-with-twelvelabs): the built-in Marengo functions.
- [How Pixeltable works](https://docs.pixeltable.com/overview/how-it-works): the application file, schema commands, and service commands.
- [Serving tables over HTTP](https://docs.pixeltable.com/howto/deployment/serving): `FastAPIRouter`, query routes, and generated API documentation.
- [Building Cross-Modal Video Search with TwelveLabs and Pixeltable](https://www.twelvelabs.io/blog/twelve-labs-and-pixeltable): the earlier tutorial, in notebook form.

<!-- Images still to capture (required: 80% of posts; the median post has 11): home For You row, watch page Up Next with reasons, creator page, text search results, image search results, pxt schema diff output, /docs OpenAPI page. -->

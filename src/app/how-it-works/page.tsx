"use client";

import { useState } from "react";

const REPO_URL = "https://github.com/mrnkim/substack-style-rec";

const sceneIndexSnippet = `video_scenes.add_embedding_index(
    "video_segment",
    embedding=marengo,
    idx_name="scene_marengo",
)`;

const analyzeSnippet = `@pxt.udf
def analyze_video(video_id: str) -> dict:
    # calls Twelve Labs Analyze API, returns {topic, style, tone}

videos.add_computed_column(raw_attributes=analyze_video(videos.id))
videos.add_computed_column(topic=videos.raw_attributes["topic"])
videos.add_computed_column(style=videos.raw_attributes["style"])
videos.add_computed_column(tone=videos.raw_attributes["tone"])`;

const similaritySnippet = `sim = video_scenes.video_segment.similarity(string=query)
results = video_scenes.order_by(sim, asc=False).limit(20).collect()`;

function CodeBlock({
  label,
  code,
  caption,
}: {
  label: string;
  code: string;
  caption: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard write can fail in some sandboxed contexts — silently no-op
    }
  };

  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border-light)]">
        <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide">
          {label}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={`Copy ${label} snippet to clipboard`}
          className="text-xs text-[var(--text-tertiary)] hover:text-[var(--accent)] transition-colors"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre
        tabIndex={0}
        className="px-4 py-4 overflow-x-auto text-xs leading-relaxed text-[var(--text-primary)] font-[family-name:var(--font-mono)]"
      >
        <code>{code}</code>
      </pre>
      <div className="px-4 py-3 border-t border-[var(--border-light)] text-xs text-[var(--text-secondary)] leading-relaxed">
        {caption}
      </div>
    </div>
  );
}

function StepCard({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center pt-1">
        <div className="w-7 h-7 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-xs font-semibold text-[var(--accent)]">
          {number}
        </div>
        {number < 4 && (
          <div className="w-px flex-1 bg-[var(--border-default)] mt-2 min-h-12" />
        )}
      </div>
      <div className="pb-8 flex-1">
        <h3 className="text-base font-semibold text-[var(--text-primary)] mb-1">
          {title}
        </h3>
        <div className="text-sm text-[var(--text-secondary)] leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
}

function ResourceTile({
  href,
  emoji,
  title,
  description,
}: {
  href: string;
  emoji: string;
  title: string;
  description: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group block p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)] hover:border-[var(--border-accent)] hover:bg-[var(--bg-elevated)] transition-colors"
    >
      <div className="text-2xl mb-3">{emoji}</div>
      <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors mb-1">
        {title}
      </div>
      <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
        {description}
      </div>
    </a>
  );
}

export default function HowItWorksPage() {
  return (
    <div className="pb-20 animate-fade-up">
      {/* Hero */}
      <section className="px-8 pt-10 pb-8 max-w-4xl">
        <h1 className="text-4xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-6">
          How it works
        </h1>

        <div className="flex flex-wrap gap-2 mb-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] text-xs font-medium text-[var(--accent)]">
            <span aria-hidden>⬡</span>
            TwelveLabs · Marengo 3.0 + Analyze
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] text-xs font-medium text-[var(--accent)]">
            <span aria-hidden>◆</span>
            Pixeltable · multimodal backend for AI apps
          </span>
        </div>

        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-[var(--radius-md)] bg-[var(--accent)] text-[var(--text-inverse)] text-sm font-semibold hover:bg-[var(--accent-hover)] transition-colors"
        >
          View source on GitHub
          <span aria-hidden>↗</span>
        </a>
      </section>

      <div className="space-y-16">
        {/* The two pieces */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
            The stack
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-6 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg text-[var(--accent)]" aria-hidden>⬡</span>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  TwelveLabs
                </h3>
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                TwelveLabs builds models that watch and understand video the way you would —
                they pick up on what&apos;s being said, what&apos;s on screen, and how it all fits
                together. Two of their APIs matter here: Marengo (which turns a video clip into
                a searchable embedding) and Analyze (which pulls out structured details
                like topic, style, and tone).
              </p>
              <div className="mt-4 flex gap-4 text-xs font-medium">
                <a
                  href="https://docs.twelvelabs.io"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  Docs →
                </a>
                <a
                  href="https://github.com/twelvelabs-io/twelvelabs-python"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  GitHub →
                </a>
              </div>
            </div>

            <div className="p-6 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg text-[var(--accent)]" aria-hidden>◆</span>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  Pixeltable
                </h3>
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                Pixeltable is a multimodal backend for AI apps in Python, created by the team
                behind Apache Parquet and Apache Impala (Apache 2.0 license). In this app,
                the videos, embeddings, and Analyze results all live in Pixeltable tables.
                When a new video is added, Pixeltable keeps everything in sync — it calls
                Marengo, runs Analyze, and updates the index without any extra plumbing.
              </p>
              <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs font-medium">
                <a
                  href="https://docs.pixeltable.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  Docs →
                </a>
                <a
                  href="https://github.com/pixeltable/pixeltable"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  GitHub →
                </a>
                <a
                  href="https://github.com/pixeltable/pixeltable-starter-kit"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  Starter kit →
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Architecture: responsibilities + flow */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
            Architecture
          </h2>

          {/* Responsibility grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-10">
            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base text-[var(--accent)]" aria-hidden>⬡</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  TwelveLabs
                </h3>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1.5">
                <li>Turns each video scene into a 512-dim vector (Marengo 3.0)</li>
                <li>Extracts topic, style, and tone from each video (Analyze API)</li>
                <li>Hosts the uploaded videos and serves HLS streams</li>
              </ul>
            </div>

            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-accent)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base text-[var(--accent)]" aria-hidden>◆</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Pixeltable
                </h3>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1.5">
                <li>Stores videos, embeddings, and Analyze results in one place — no separate vector DB or file store</li>
                <li>Runs similarity queries against the embedding index</li>
                <li>Mixes subscribed and new creators (70/30) so recommendations stay diverse</li>
                <li>Generates the &ldquo;Because you watched&hellip;&rdquo; explanation text</li>
              </ul>
            </div>

            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base text-[var(--text-secondary)]" aria-hidden>○</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Frontend (Next.js)
                </h3>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1.5">
                <li>Tracks which creators you subscribe to and what you&apos;ve watched</li>
                <li>Renders all the pages, handles navigation</li>
                <li>Saves your state in the browser so it survives a refresh</li>
              </ul>
            </div>
          </div>

          {/* Four-step flow */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-5">
              From raw video to recommendation, in four steps
            </h3>
            <div className="border-l-0">
              <StepCard number={1} title="Ingest">
                25 longform videos from 11 creators, sourced from YouTube, get loaded
                into Pixeltable along with metadata about each creator. The mix covers
                interviews, commentary, creative, and educational content.
              </StepCard>
              <StepCard number={2} title="Scene-split">
                Pixeltable detects natural scene boundaries in each video and splits
                it into roughly 10 shorter clips. This means search and recommendations
                can match on specific moments, not just whole videos.
              </StepCard>
              <StepCard number={3} title="Embed + analyze">
                Marengo 3.0 turns each scene clip into a searchable embedding. The
                Analyze API watches each full video and tags it with a topic, style,
                and tone. Both happen automatically when a video is added.
              </StepCard>
              <StepCard number={4} title="Serve">
                When you open the app, recommendations come from similarity queries
                against those pre-computed embeddings. The backend caps each creator
                at 2 results and mixes in new creators you haven&apos;t subscribed to,
                then writes a short{" "}
                <em className="text-[var(--text-primary)]">&ldquo;Because you watched&hellip;&rdquo;</em>{" "}
                explanation for each pick.
              </StepCard>
            </div>
          </div>
        </section>

        {/* When TwelveLabs runs */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-1">
            Runtime
          </h2>
          <h3 className="text-2xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-3">
            When TwelveLabs gets called
          </h3>
          <p className="text-sm text-[var(--text-secondary)] mb-6 max-w-2xl">
            Two places: once per video at ingest, and once per text search query. Recommendation
            queries run against embeddings Pixeltable already has, so the homepage, watch page,
            and creator catalogs don&apos;t trigger a TwelveLabs call.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="text-[11px] font-medium text-[var(--accent)] uppercase tracking-wide mb-2">
                At ingest · once
              </div>
              <div className="text-sm text-[var(--text-primary)] font-semibold mb-2">
                Upload, embed, and analyze
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Every video goes through TwelveLabs once when it&apos;s first added.
                The embeddings and attributes are stored locally after that.
              </p>
            </div>
            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="text-[11px] font-medium text-[var(--accent)] uppercase tracking-wide mb-2">
                At search · live
              </div>
              <div className="text-sm text-[var(--text-primary)] font-semibold mb-2">
                One API call per search
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Your search text gets turned into an embedding via Marengo so it can be
                compared against the video scenes. Matching happens locally.
              </p>
            </div>
            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-wide mb-2">
                For recommendations · never
              </div>
              <div className="text-sm text-[var(--text-primary)] font-semibold mb-2">
                No live calls
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Homepage, watch page, and creator catalogs all serve from pre-computed
                embeddings.
              </p>
            </div>
          </div>
        </section>

        {/* Integration code */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
            Integration code
          </h2>
          <div className="space-y-4">
            <CodeBlock
              label="Embedding each scene"
              code={sceneIndexSnippet}
              caption="Pixeltable computes the Marengo embedding for every scene, including any added later, and keeps the index current."
            />
            <CodeBlock
              label="Analyze API as a computed column"
              code={analyzeSnippet}
              caption="The Analyze API call is wrapped as a Python function and attached as a computed column. Pixeltable calls it automatically whenever a new video is inserted."
            />
            <CodeBlock
              label="Searching scenes by text"
              code={similaritySnippet}
              caption="A text query gets embedded by Marengo into the same vector space as the video scenes, so you can search across modalities in two lines."
            />
          </div>
        </section>

        {/* Resources */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
            Resources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <ResourceTile
              href="https://docs.twelvelabs.io"
              emoji="⬡"
              title="TwelveLabs docs"
              description="Marengo embeddings, Analyze API, and video indexing."
            />
            <ResourceTile
              href="https://docs.pixeltable.com"
              emoji="◆"
              title="Pixeltable docs"
              description="Learn how to build your own app with Pixeltable."
            />
            <ResourceTile
              href="https://docs.pixeltable.com/howto/providers/working-with-twelvelabs.md"
              emoji="📗"
              title="Pixeltable + TwelveLabs guide"
              description="Walkthrough for wiring the two together."
            />
            <ResourceTile
              href={REPO_URL}
              emoji="💻"
              title="This app on GitHub"
              description="Full source for the demo."
            />
          </div>
        </section>
      </div>
    </div>
  );
}

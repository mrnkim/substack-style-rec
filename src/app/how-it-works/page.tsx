"use client";

import { useState } from "react";

const REPO_URL = "https://github.com/apreshill/substack-style-rec";

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
        <h1 className="text-4xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-3">
          How it works
        </h1>
        <p className="text-base text-[var(--text-secondary)] leading-relaxed max-w-2xl mb-6">
          This demo recommends videos using{" "}
          <span className="text-[var(--text-primary)]">TwelveLabs Marengo</span> embeddings,
          with <span className="text-[var(--text-primary)]">Pixeltable</span> as the data layer.
        </p>

        <div className="flex flex-wrap gap-2 mb-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] text-xs font-medium text-[var(--accent)]">
            <span aria-hidden>⬡</span>
            TwelveLabs · Marengo 3.0 + Analyze
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)] text-xs font-medium text-[var(--accent)]">
            <span aria-hidden>◆</span>
            Pixeltable · Python data layer
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
                Marengo 3.0 for multimodal video embeddings, and Analyze for structured
                per-video attributes ({" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  topic
                </code>
                ,{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  style
                </code>
                ,{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  tone
                </code>
                ).
              </p>
            </div>

            <div className="p-6 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg text-[var(--accent)]" aria-hidden>◆</span>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  Pixeltable
                </h3>
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
                Pixeltable is a Python data layer for AI applications. You define tables with
                computed columns, including embedding indexes, and Pixeltable runs the model
                and keeps the index up to date as new data arrives.
              </p>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                In this app, every TwelveLabs call (embeddings, Analyze) is a Pixeltable
                computed column. Recommendation queries are{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  .similarity()
                </code>{" "}
                calls against the local pgvector index.
              </p>
              <div className="mt-4 flex gap-4 text-xs font-medium">
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
                <span className="text-base text-[var(--text-secondary)]" aria-hidden>○</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Frontend (Next.js)
                </h3>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1.5">
                <li>Subscription state, watch history</li>
                <li>UI, navigation, animations</li>
                <li>localStorage persistence</li>
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
                <li>Video storage, computed columns</li>
                <li>Embedding indexes, .similarity()</li>
                <li>70/30 split, creator diversity</li>
                <li>Reason generation</li>
              </ul>
            </div>

            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base text-[var(--accent)]" aria-hidden>⬡</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  TwelveLabs
                </h3>
              </div>
              <ul className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-1.5">
                <li>Marengo 3.0 embeddings</li>
                <li>Analyze API attribute extraction</li>
                <li>Upload + indexing</li>
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
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  yt-dlp
                </code>{" "}
                downloads 25 curated videos and{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  setup_pixeltable.py
                </code>{" "}
                inserts them into a Pixeltable{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  videos
                </code>{" "}
                table alongside a{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  creators
                </code>{" "}
                table.
              </StepCard>
              <StepCard number={2} title="Scene-split">
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  scene_detect_histogram
                </code>{" "}
                finds natural scene boundaries.{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  video_splitter(mode=&quot;fast&quot;)
                </code>{" "}
                cuts at those points using stream copy (no re-encoding). The result is a{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  video_scenes
                </code>{" "}
                view with about 10 scenes per video.
              </StepCard>
              <StepCard number={3} title="Embed + analyze">
                Pixeltable computes Marengo 3.0 embeddings on every scene segment and runs the
                TwelveLabs Analyze API on every video. Both are{" "}
                <span className="text-[var(--text-primary)]">computed columns</span>, so they
                populate automatically on{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  INSERT
                </code>
                . Scene embeddings land in the{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  scene_marengo
                </code>{" "}
                index. A{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  title_marengo
                </code>{" "}
                text index sits alongside as a fallback.
              </StepCard>
              <StepCard number={4} title="Serve">
                FastAPI routes run{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  .similarity()
                </code>{" "}
                against the pre-computed{" "}
                <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
                  scene_marengo
                </code>{" "}
                index, apply creator diversity (max 2 per creator) and a 70/30
                subscription/discovery split, and use the Analyze attributes to build the{" "}
                <em className="text-[var(--text-primary)]">&ldquo;Because you watched…&rdquo;</em>{" "}
                reason text.
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
                Upload, Embed, Analyze
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Every video runs through TwelveLabs once when it&apos;s added, via Pixeltable
                computed columns. The results stay in the index.
              </p>
            </div>
            <div className="p-5 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)]">
              <div className="text-[11px] font-medium text-[var(--accent)] uppercase tracking-wide mb-2">
                At search · live
              </div>
              <div className="text-sm text-[var(--text-primary)] font-semibold mb-2">
                One Embed call per query
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Pixeltable embeds the search query into a 512-dim vector via Marengo. The local
                pgvector index does the rest.
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
              label="Per-scene Marengo embedding index"
              code={sceneIndexSnippet}
              caption="Pixeltable computes the embedding for every existing row and every future insert, and keeps the index up to date."
            />
            <CodeBlock
              label="TwelveLabs Analyze as a Pixeltable UDF"
              code={analyzeSnippet}
              caption="Wrap an external API as a UDF, then expose it as a computed column. Pixeltable handles the calls as new rows arrive."
            />
            <CodeBlock
              label="Cross-modal scene similarity"
              code={similaritySnippet}
              caption="Search a text query against video scene embeddings. Marengo 3.0 puts text and video in the same 512-dim space, so this works without any cross-modal bridging code."
            />
          </div>
        </section>

        {/* Content */}
        <section className="px-8 max-w-4xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-3">
            Content
          </h2>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            25 longform videos from 11 creators across four categories: interview (40%),
            commentary (30%), creative (20%), educational (10%). The list lives in{" "}
            <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
              scripts/curate_videos.csv
            </code>
            , downloaded with{" "}
            <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
              yt-dlp
            </code>{" "}
            and indexed in the TwelveLabs index{" "}
            <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
              69c37b6708cd679f8afbd748
            </code>
            .
          </p>
        </section>

        {/* Frontend */}
        <section className="px-8 max-w-4xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-3">
            Frontend
          </h2>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, and{" "}
            <code className="text-[11px] font-[family-name:var(--font-mono)] text-[var(--text-primary)]">
              hls.js
            </code>{" "}
            for video playback. Full source is in the{" "}
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
            >
              repo
            </a>
            .
          </p>
        </section>

        {/* Resources */}
        <section className="px-8 max-w-5xl">
          <h2 className="text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
            Resources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <ResourceTile
              href="https://docs.pixeltable.com/howto/providers/working-with-twelvelabs.md"
              emoji="📗"
              title="Pixeltable + TwelveLabs guide"
              description="Official walkthrough for wiring TwelveLabs into Pixeltable."
            />
            <ResourceTile
              href="https://docs.pixeltable.com"
              emoji="📘"
              title="Pixeltable docs"
              description="Tables, computed columns, embedding indexes, UDFs."
            />
            <ResourceTile
              href="https://github.com/pixeltable/pixeltable"
              emoji="◆"
              title="Pixeltable on GitHub"
              description="Source, examples, issue tracker."
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

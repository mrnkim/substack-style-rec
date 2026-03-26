"use client";

import Link from "next/link";
import type { Video } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

interface HeroFeatureProps {
  video: Video;
}

export function HeroFeature({ video }: HeroFeatureProps) {
  return (
    <div className="relative w-full h-[65vh] min-h-[400px] max-h-[600px] overflow-hidden animate-fade-up">
      {/* Background thumbnail */}
      <img
        src={video.thumbnailUrl}
        alt=""
        className="absolute inset-0 w-full h-full object-cover scale-110 blur-sm"
      />

      {/* Gradient overlays */}
      <div className="hero-gradient absolute inset-0" />
      <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-primary)]/80 via-transparent to-transparent" />

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col justify-end px-8 pb-12 max-w-2xl">
        {/* Category + Duration */}
        <div className="flex items-center gap-3 mb-4">
          <span className={`px-2.5 py-1 text-xs font-semibold rounded-full pill-${video.category}`}>
            {video.category}
          </span>
          <span className="text-xs font-mono text-[var(--text-secondary)]">
            {formatDuration(video.duration)}
          </span>
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-bold leading-tight tracking-tight text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-3">
          {video.title}
        </h1>

        {/* Creator */}
        <div className="flex items-center gap-2 mb-5">
          <div className="w-6 h-6 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
            <span className="text-[10px] font-bold text-[var(--text-secondary)]">
              {video.creator.name[0]}
            </span>
          </div>
          <Link
            href={`/creator/${video.creator.id}`}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
          >
            {video.creator.name}
          </Link>
        </div>

        {/* Topics */}
        {video.attributes && video.attributes.topic.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {video.attributes.topic.map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 text-[11px] text-[var(--text-tertiary)] bg-[var(--bg-card)] rounded-full border border-[var(--border-default)]"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Link
            href={`/watch/${video.id}`}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-[var(--accent)] text-[var(--text-inverse)] font-semibold text-sm transition-all hover:bg-[var(--accent-hover)] hover:-translate-y-0.5 shadow-lg"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M4 2L14 8L4 14V2Z" fill="currentColor" />
            </svg>
            Watch Now
          </Link>
          <Link
            href={`/creator/${video.creator.id}`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[var(--text-primary)] text-sm font-medium transition-all hover:bg-[var(--bg-hover)] hover:border-[var(--text-tertiary)]"
          >
            More Info
          </Link>
        </div>
      </div>
    </div>
  );
}

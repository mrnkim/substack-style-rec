"use client";

import Link from "next/link";
import type { Video } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

interface VideoCardProps {
  video: Video;
  href?: string;
  thumbnailOverride?: string;
  reason?: string;
  matchedAttributes?: string[];
  videoTags?: string[];
  contextTag?: string | null;
  source?: "subscription" | "discovery";
  score?: number;
  showCreator?: boolean;
  size?: "sm" | "md" | "lg";
}

const sizeStyles = {
  sm: "w-[220px]",
  md: "w-[280px]",
  lg: "w-[340px]",
};

export function VideoCard({
  video,
  href,
  thumbnailOverride,
  reason,
  matchedAttributes,
  videoTags,
  contextTag,
  source,
  score,
  showCreator = true,
  size = "md",
}: VideoCardProps) {
  const thumbnail = thumbnailOverride || video.thumbnailUrl;
  const matchPct =
    typeof score === "number" && score > 0
      ? Math.min(100, Math.max(0, Math.round(score * 100)))
      : null;
  const sharedTags = matchedAttributes ?? [];
  const fallbackTags = videoTags ?? [];
  const tagsToShow = sharedTags.length > 0 ? sharedTags : fallbackTags;
  const tagsLabel = sharedTags.length > 0 ? "Common Tags" : "About This Video";
  const hasRecBlock = !!reason || matchPct !== null;
  return (
    <Link href={href ?? `/watch/${video.id}`} className={`video-card block ${sizeStyles[size]} group`}>
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-lg overflow-hidden bg-[var(--bg-elevated)]">
        {thumbnail ? (
          <img
            src={thumbnail}
            alt={video.title}
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-[var(--text-tertiary)]">
            <svg className="w-10 h-10" viewBox="0 0 16 16" fill="none">
              <rect x="1" y="3" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
              <path d="M11 6.5l4-2v7l-4-2V6.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
            </svg>
          </div>
        )}
        {/* Duration badge */}
        <span className="absolute bottom-2 right-2 px-1.5 py-0.5 text-[10px] font-mono font-medium bg-black/70 text-[var(--text-primary)] rounded">
          {formatDuration(video.duration)}
        </span>

        {/* Play overlay */}
        <div className="thumb-overlay rounded-lg">
          <div className="w-10 h-10 rounded-full bg-[var(--accent)] flex items-center justify-center shadow-lg">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4 2L14 8L4 14V2Z" fill="#1D1C1B" />
            </svg>
          </div>
        </div>

        {/* Category pill */}
        <span
          className={`absolute top-2 left-2 px-2 py-0.5 text-[10px] font-medium rounded-full pill-${video.category}`}
        >
          {video.category}
        </span>
      </div>

      {/* Info */}
      <div className="mt-2.5 space-y-1">
        <h3 className="text-sm font-medium text-[var(--text-primary)] leading-snug line-clamp-2 group-hover:text-[var(--accent)] transition-colors">
          {video.title}
        </h3>

        {showCreator && (
          <div className="flex items-center gap-1.5">
            {/* Creator avatar placeholder */}
            <div className="w-4 h-4 rounded-full bg-[var(--bg-elevated)] flex items-center justify-center">
              <span className="text-[8px] font-bold text-[var(--text-tertiary)]">
                {video.creator.name[0]}
              </span>
            </div>
            <span className="text-xs text-[var(--text-secondary)]">{video.creator.name}</span>
          </div>
        )}

        {/* Recommendation reason + match score + tags */}
        {hasRecBlock && (
          <div className="mt-2 p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] space-y-1.5">
            <div className="flex items-center gap-1.5">
              {source && (
                <span
                  className={`inline-block shrink-0 px-1.5 py-0.5 text-[9px] font-semibold rounded-sm uppercase tracking-wider ${
                    source === "subscription" ? "badge-subscription" : "badge-discovery"
                  }`}
                >
                  {source === "subscription" ? "Following" : "Discover"}
                </span>
              )}
              {matchPct !== null && (
                <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                  Video Match:{" "}
                  <span className="text-[var(--accent)]">{matchPct}</span>
                </span>
              )}
            </div>
            {reason && (
              <p className="text-[11px] leading-snug text-[var(--text-secondary)] line-clamp-3">
                {reason}
              </p>
            )}
            {tagsToShow.length > 0 && (
              <div className="pt-1.5 border-t border-[var(--border-light)]">
                <div className="flex items-center gap-1 mb-1.5">
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 16 16"
                    fill="none"
                    className="text-[var(--accent)]"
                    aria-hidden
                  >
                    <path
                      d="M2 6.5V2.5C2 2.22 2.22 2 2.5 2h4l7 7-4.5 4.5L2 6.5z"
                      stroke="currentColor"
                      strokeWidth="1.4"
                      strokeLinejoin="round"
                    />
                    <circle cx="5" cy="5" r="1" fill="currentColor" />
                  </svg>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                    {tagsLabel}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {tagsToShow.map((attr) => (
                    <span key={attr} className="attr-pill">
                      {attr}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {contextTag && (
              <p className="text-[10px] text-[var(--text-tertiary)] italic">
                {contextTag}
              </p>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}

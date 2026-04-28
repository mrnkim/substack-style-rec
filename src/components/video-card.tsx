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
  source?: "subscription" | "discovery";
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
  source,
  showCreator = true,
  size = "md",
}: VideoCardProps) {
  const thumbnail = thumbnailOverride || video.thumbnailUrl;
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

        {/* Recommendation reason + attributes */}
        {reason && (
          <div className="mt-1.5 space-y-1.5">
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
              <span className="text-[11px] text-[var(--text-tertiary)] line-clamp-2">{reason}</span>
            </div>
            {matchedAttributes && matchedAttributes.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {matchedAttributes.map((attr) => (
                  <span
                    key={attr}
                    className="attr-pill"
                  >
                    {attr}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}

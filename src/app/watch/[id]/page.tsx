"use client";

import { use, useEffect } from "react";
import Link from "next/link";
import { getVideoById, getSimilarVideos } from "@/lib/mock-data";
import { useUserState } from "@/lib/user-state";
import { SubscribeButton } from "@/components/subscribe-button";
import { VideoCard } from "@/components/video-card";
import { formatDuration, timeAgo } from "@/lib/utils";

export default function WatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const video = getVideoById(id);
  const { markWatched } = useUserState();
  const similar = getSimilarVideos(id);

  useEffect(() => {
    if (video) markWatched(video.id);
  }, [video, markWatched]);

  if (!video) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <p className="text-[var(--text-secondary)]">Video not found</p>
      </div>
    );
  }

  return (
    <div className="pb-16 animate-fade-up">
      <div className="flex flex-col lg:flex-row gap-6 px-8 pt-6">
        {/* Main player area */}
        <div className="flex-1 min-w-0">
          {/* Player placeholder */}
          <div
            className="aspect-video rounded-xl overflow-hidden relative"
            style={{ background: video.thumbnailGradient }}
          >
            {/* Play button centered */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-[var(--accent)] flex items-center justify-center shadow-2xl cursor-pointer transition-transform hover:scale-110">
                <svg width="24" height="24" viewBox="0 0 16 16" fill="none">
                  <path d="M4 2L14 8L4 14V2Z" fill="#1D1C1B" />
                </svg>
              </div>
            </div>

            {/* Duration */}
            <span className="absolute bottom-3 right-3 px-2 py-1 text-xs font-mono bg-black/70 text-[var(--text-primary)] rounded">
              {formatDuration(video.duration)}
            </span>
          </div>

          {/* Video info */}
          <div className="mt-5 space-y-4">
            <h1 className="text-2xl font-bold text-[var(--text-primary)] leading-tight font-[family-name:var(--font-display)] italic">
              {video.title}
            </h1>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Link
                  href={`/creator/${video.creator.id}`}
                  className="flex items-center gap-2 group"
                >
                  <div className="w-9 h-9 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
                    <span className="text-sm font-bold text-[var(--text-tertiary)]">
                      {video.creator.name[0]}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors">
                      {video.creator.name}
                    </span>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      {timeAgo(video.uploadDate)}
                    </p>
                  </div>
                </Link>
                <SubscribeButton creatorId={video.creator.id} size="sm" />
              </div>

              {/* Category pill */}
              <span className={`px-3 py-1 text-xs font-medium rounded-full pill-${video.category}`}>
                {video.category}
              </span>
            </div>

            {/* Attributes */}
            <div className="p-4 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)]">
              <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
                About this video
              </h3>
              <div className="flex flex-wrap gap-2">
                {video.attributes.topic.map((t) => (
                  <span
                    key={t}
                    className="px-2 py-0.5 text-xs text-[var(--text-secondary)] bg-[var(--bg-elevated)] rounded-full"
                  >
                    {t}
                  </span>
                ))}
                <span className="px-2 py-0.5 text-xs text-[var(--accent)] bg-[var(--accent-muted)] rounded-full">
                  {video.attributes.style}
                </span>
                <span className="px-2 py-0.5 text-xs text-[var(--text-tertiary)] bg-[var(--bg-elevated)] rounded-full">
                  {video.attributes.tone}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar — similar videos */}
        <aside className="w-full lg:w-[340px] flex-shrink-0">
          <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
            Up Next
          </h2>
          <div className="space-y-4 stagger">
            {similar.map((rec) => (
              <div key={rec.video.id} className="animate-fade-up">
                <VideoCard
                  video={rec.video}
                  reason={rec.reason}
                  source={rec.source}
                  size="sm"
                />
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}

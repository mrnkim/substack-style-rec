"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getVideo, getVideos } from "@/lib/api";
import { useUserState } from "@/lib/user-state";
import { SubscribeButton } from "@/components/subscribe-button";
import { VideoCard } from "@/components/video-card";
import { VideoPlayer } from "@/components/video-player";
import { timeAgo } from "@/lib/utils";
import type { Video, Recommendation } from "@/lib/types";

export default function WatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { markWatched } = useUserState();
  const [video, setVideo] = useState<Video | null>(null);
  const [similar, setSimilar] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getVideo(id), getVideos()]).then(([v, allVideos]) => {
      setVideo(v);
      if (v) {
        // Simple similarity: same category or same creator, excluding current
        const recs = allVideos
          .filter((other) => other.id !== v.id)
          .map((other) => {
            const sameCreator = other.creator.id === v.creator.id;
            const sameCategory = other.category === v.category;
            const score = (sameCreator ? 0.4 : 0) + (sameCategory ? 0.3 : 0) + Math.random() * 0.2;
            return {
              video: other,
              score,
              reason: sameCreator
                ? `More from ${other.creator.name}`
                : sameCategory
                  ? `Similar ${other.category} content`
                  : "You might also enjoy",
              matchedAttributes: [] as string[],
              source: sameCreator ? ("subscription" as const) : ("discovery" as const),
            };
          })
          .sort((a, b) => b.score - a.score)
          .slice(0, 8);
        setSimilar(recs);
      }
      setLoading(false);
    });
  }, [id]);

  useEffect(() => {
    if (video) markWatched(video.id);
  }, [video, markWatched]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

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
          {/* Video Player */}
          <VideoPlayer
            hlsUrl={video.hlsUrl}
            thumbnailUrl={video.thumbnailUrl}
            title={video.title}
            duration={video.duration}
          />

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

            {/* Attributes — shown when available from Analyze API */}
            {video.attributes && (
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
            )}
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

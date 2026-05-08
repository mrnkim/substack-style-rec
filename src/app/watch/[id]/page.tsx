"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getVideo, getSimilarVideos } from "@/lib/api";
import { useUserState } from "@/lib/user-state";
import { SubscribeButton } from "@/components/subscribe-button";
import { VideoCard } from "@/components/video-card";
import { VideoPlayer, type VideoPlayerHandle } from "@/components/video-player";
import { formatDuration, timeAgo } from "@/lib/utils";
import type { Video, Recommendation } from "@/lib/types";

export default function WatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const startTime = Number(searchParams.get("t")) || 0;
  const { markWatched, watchHistory, isSubscribed } = useUserState();
  const [video, setVideo] = useState<Video | null>(null);
  const [similar, setSimilar] = useState<Recommendation[]>([]);
  const [videoLoading, setVideoLoading] = useState(true);
  const [similarLoading, setSimilarLoading] = useState(true);
  const watchHistoryRef = useRef(watchHistory);
  watchHistoryRef.current = watchHistory;
  const playerRef = useRef<VideoPlayerHandle>(null);

  useEffect(() => {
    let cancelled = false;
    setVideoLoading(true);
    setSimilarLoading(true);
    setVideo(null);
    setSimilar([]);

    getVideo(id)
      .then((v) => {
        if (!cancelled) setVideo(v);
      })
      .finally(() => {
        if (!cancelled) setVideoLoading(false);
      });

    getSimilarVideos(id, watchHistoryRef.current, 8)
      .then((recs) => {
        if (!cancelled) setSimilar(recs);
      })
      .finally(() => {
        if (!cancelled) setSimilarLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (video) markWatched(video.id);
  }, [video, markWatched]);

  if (videoLoading) {
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
            ref={playerRef}
            hlsUrl={video.hlsUrl}
            thumbnailUrl={video.thumbnailUrl}
            title={video.title}
            duration={video.duration}
            startTime={startTime}
          />

          {/* Video info */}
          <div className="mt-5 space-y-4">
            <h1 className="text-2xl font-bold text-[var(--text-primary)] leading-tight font-[family-name:var(--font-brand)]">
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

            {/* Summary — TL Generate API */}
            {video.summary && (
              <div className="p-4 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)]">
                <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
                  Summary
                </h3>
                <p className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-line">
                  {video.summary}
                </p>
              </div>
            )}

            {/* Chapters — click to seek */}
            {video.chapters && video.chapters.length > 0 && (
              <div className="p-4 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)]">
                <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                  Chapters
                </h3>
                <ul className="space-y-1">
                  {video.chapters.map((ch, i) => (
                    <li key={`${ch.start}-${i}`}>
                      <button
                        onClick={() => playerRef.current?.seekTo(ch.start)}
                        className="w-full text-left flex items-start gap-3 px-3 py-2 rounded-md hover:bg-[var(--bg-hover)] transition-colors group cursor-pointer"
                      >
                        <span className="shrink-0 mt-0.5 text-xs font-mono font-medium text-[var(--accent)] tabular-nums w-12">
                          {formatDuration(Math.round(ch.start))}
                        </span>
                        <span className="flex-1 min-w-0">
                          <span className="block text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors leading-snug">
                            {ch.title || `Chapter ${i + 1}`}
                          </span>
                          {ch.summary && (
                            <span className="block mt-0.5 text-xs text-[var(--text-tertiary)] leading-relaxed line-clamp-2">
                              {ch.summary}
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar — similar videos */}
        <aside className="w-full lg:w-[340px] flex-shrink-0">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
              Up Next
            </h2>
            {similarLoading && (
              <div className="w-3.5 h-3.5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            )}
          </div>
          {similarLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-video rounded-lg bg-[var(--bg-elevated)]" />
                  <div className="mt-2.5 space-y-1.5">
                    <div className="h-3.5 rounded bg-[var(--bg-elevated)] w-5/6" />
                    <div className="h-3 rounded bg-[var(--bg-elevated)] w-2/5" />
                  </div>
                </div>
              ))}
            </div>
          ) : similar.length === 0 ? (
            <p className="text-sm text-[var(--text-tertiary)]">
              No similar videos yet.
            </p>
          ) : (
            <div className="space-y-4 stagger">
              {similar.map((rec) => {
                // Recompute subscription-derived fields client-side so the
                // badge and contextTag react to live subscription toggles
                // without re-fetching /similar.
                const subscribed = isSubscribed(rec.video.creator.id);
                const liveSource = subscribed ? "subscription" : "discovery";
                const liveContextTag = subscribed
                  ? "From your subscriptions"
                  : rec.contextTag;
                return (
                  <div key={rec.video.id} className="animate-fade-up">
                    <VideoCard
                      video={rec.video}
                      reason={rec.reason}
                      matchedAttributes={rec.matchedAttributes}
                      videoTags={rec.videoTags}
                      contextTag={liveContextTag}
                      source={liveSource}
                      score={rec.score}
                      size="sm"
                    />
                  </div>
                );
              })}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

"use client";

import { use } from "react";
import Link from "next/link";
import { getCreatorById, getVideosByCreator } from "@/lib/mock-data";
import { SubscribeButton } from "@/components/subscribe-button";
import { VideoCard } from "@/components/video-card";
import { categoryLabel } from "@/lib/utils";

export default function CreatorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const creator = getCreatorById(id);
  const creatorVideos = getVideosByCreator(id);

  if (!creator) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <p className="text-[var(--text-secondary)]">Creator not found</p>
      </div>
    );
  }

  // Group by category
  const grouped = creatorVideos.reduce(
    (acc, video) => {
      if (!acc[video.category]) acc[video.category] = [];
      acc[video.category].push(video);
      return acc;
    },
    {} as Record<string, typeof creatorVideos>,
  );

  return (
    <div className="pb-16 animate-fade-up">
      {/* Creator header */}
      <div className="relative px-8 pt-12 pb-8">
        {/* Background accent glow */}
        <div
          className="absolute top-0 left-0 right-0 h-48 opacity-30"
          style={{
            background:
              "radial-gradient(ellipse at 30% 0%, var(--accent) 0%, transparent 60%)",
          }}
        />

        <div className="relative z-10 flex items-start gap-6">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-default)] flex items-center justify-center flex-shrink-0 shadow-lg">
            <span className="text-3xl font-bold text-[var(--text-tertiary)]">
              {creator.name[0]}
            </span>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-4 mb-2">
              <h1 className="text-2xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-display)] italic">
                {creator.name}
              </h1>
              <SubscribeButton creatorId={creator.id} />
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-xl leading-relaxed">
              {creator.description}
            </p>
            <div className="flex items-center gap-4 mt-3 text-xs text-[var(--text-tertiary)]">
              <span>{creator.videoCount} videos</span>
              <span className="w-1 h-1 rounded-full bg-[var(--text-tertiary)]" />
              <span>
                {Object.keys(grouped)
                  .map(categoryLabel)
                  .join(", ")}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Video grid */}
      <div className="px-8 mt-4 space-y-10">
        {/* All videos */}
        <section>
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            All Episodes
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5 stagger">
            {creatorVideos.map((video) => (
              <VideoCard key={video.id} video={video} showCreator={false} size="md" />
            ))}
          </div>
        </section>

        {/* By category */}
        {Object.entries(grouped).map(([category, categoryVideos]) => (
          <section key={category}>
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              {categoryLabel(category)}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
              {categoryVideos.map((video) => (
                <VideoCard key={video.id} video={video} showCreator={false} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

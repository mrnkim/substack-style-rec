"use client";

import { useEffect, useState } from "react";
import { getVideos, getCreators } from "@/lib/api";
import { useUserState } from "@/lib/user-state";
import { CreatorCard } from "@/components/creator-card";
import { VideoRow } from "@/components/video-row";
import type { Video, Creator, Recommendation } from "@/lib/types";

export default function ExplorePage() {
  const { subscriptions } = useUserState();
  const [videos, setVideos] = useState<Video[]>([]);
  const [creators, setCreators] = useState<Creator[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getVideos(), getCreators()]).then(([v, c]) => {
      setVideos(v);
      setCreators(c);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const unsubscribedCreators = creators.filter((c) => !subscriptions.includes(c.id));
  const subscribedCreators = creators.filter((c) => subscriptions.includes(c.id));

  // Discovery videos — from unsubscribed creators
  const discoveryVideos: Recommendation[] = videos
    .filter((v) => !subscriptions.includes(v.creator.id))
    .map((video) => ({
      video,
      score: 0.85,
      reason: `Discover ${video.creator.name}`,
      matchedAttributes: video.attributes?.topic.slice(0, 2) ?? [],
      source: "discovery" as const,
    }));

  const categories = ["interview", "commentary", "creative", "educational"] as const;

  return (
    <div className="pb-16 animate-fade-up">
      {/* Header */}
      <div className="px-8 pt-10 pb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-display)] italic">
          Explore
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-2 max-w-lg">
          Discover new creators and content beyond your subscriptions.
          Recommendations powered by TwelveLabs semantic understanding.
        </p>
      </div>

      <div className="space-y-12">
        {/* Discover new creators */}
        {unsubscribedCreators.length > 0 && (
          <section className="px-8">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
              Creators to Explore
            </h2>
            <p className="text-sm text-[var(--text-tertiary)] mb-4">
              You&apos;re not subscribed to these creators yet
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger">
              {unsubscribedCreators.map((creator) => (
                <div key={creator.id} className="animate-fade-up">
                  <CreatorCard creator={creator} />
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Discovery row */}
        <VideoRow
          title="Beyond Your Subscriptions"
          subtitle="Content from creators you haven't discovered yet"
          recommendations={discoveryVideos}
          showReasons
          cardSize="lg"
        />

        {/* Browse by category */}
        {categories.map((cat) => {
          const catVideos: Recommendation[] = videos
            .filter((v) => v.category === cat)
            .map((video) => ({
              video,
              score: 0.8,
              reason: "",
              matchedAttributes: [],
              source: subscriptions.includes(video.creator.id)
                ? ("subscription" as const)
                : ("discovery" as const),
            }));

          if (catVideos.length === 0) return null;

          return (
            <VideoRow
              key={cat}
              title={cat.charAt(0).toUpperCase() + cat.slice(1)}
              recommendations={catVideos}
            />
          );
        })}

        {/* Your subscriptions */}
        {subscribedCreators.length > 0 && (
          <section className="px-8">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
              Your Subscriptions
            </h2>
            <p className="text-sm text-[var(--text-tertiary)] mb-4">
              Creators you&apos;re following
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {subscribedCreators.map((creator) => (
                <CreatorCard key={creator.id} creator={creator} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

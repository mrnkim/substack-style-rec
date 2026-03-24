"use client";

import { useUserState } from "@/lib/user-state";
import { videos, getForYouRecommendations } from "@/lib/mock-data";
import { HeroFeature } from "@/components/hero-feature";
import { VideoRow } from "@/components/video-row";
import type { Recommendation } from "@/lib/types";

export default function HomePage() {
  const { subscriptions, watchHistory } = useUserState();

  const forYou = getForYouRecommendations(subscriptions, watchHistory);
  const featured = forYou[0]?.video ?? videos[0];

  // Continue watching — last 3 watched videos
  const continueWatching: Recommendation[] = watchHistory
    .slice(-3)
    .reverse()
    .map((id) => videos.find((v) => v.id === id))
    .filter(Boolean)
    .map((video) => ({
      video: video!,
      score: 1,
      reason: "Continue watching",
      matchedAttributes: [],
      source: "subscription" as const,
    }));

  // Recently added
  const recentlyAdded: Recommendation[] = [...videos]
    .sort((a, b) => new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime())
    .slice(0, 10)
    .map((video) => ({
      video,
      score: 0.9,
      reason: "",
      matchedAttributes: [],
      source: subscriptions.includes(video.creator.id) ? ("subscription" as const) : ("discovery" as const),
    }));

  // By category
  const interviews: Recommendation[] = videos
    .filter((v) => v.category === "interview")
    .map((video) => ({
      video,
      score: 0.8,
      reason: "",
      matchedAttributes: [],
      source: "subscription" as const,
    }));

  return (
    <div className="pb-16">
      {/* Hero */}
      <HeroFeature video={featured} />

      {/* Content rows */}
      <div className="space-y-10 mt-8">
        {/* For You — main recommendation row */}
        <VideoRow
          title="For You"
          subtitle={`Based on your ${subscriptions.length} subscriptions`}
          recommendations={forYou}
          showReasons
          cardSize="lg"
        />

        {/* Continue Watching */}
        {continueWatching.length > 0 && (
          <VideoRow title="Continue Watching" recommendations={continueWatching} />
        )}

        {/* Recently Added */}
        <VideoRow title="Recently Added" recommendations={recentlyAdded} />

        {/* Deep Dives — Interviews */}
        <VideoRow
          title="Deep Dives"
          subtitle="Long-form interviews and conversations"
          recommendations={interviews}
        />
      </div>
    </div>
  );
}

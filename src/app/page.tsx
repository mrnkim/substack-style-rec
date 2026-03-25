"use client";

import { useEffect, useState } from "react";
import { useUserState } from "@/lib/user-state";
import { getVideos } from "@/lib/api";
import { HeroFeature } from "@/components/hero-feature";
import { VideoRow } from "@/components/video-row";
import type { Video, Recommendation } from "@/lib/types";

function toRec(
  video: Video,
  reason: string,
  source: "subscription" | "discovery",
  score = 0.9,
): Recommendation {
  return { video, score, reason, matchedAttributes: [], source };
}

export default function HomePage() {
  const { subscriptions, watchHistory } = useUserState();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getVideos().then((v) => {
      setVideos(v);
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

  const unwatched = videos.filter((v) => !watchHistory.includes(v.id));

  // For You — cold start or similarity-based
  const forYou: Recommendation[] = (() => {
    const subscribed = unwatched.filter((v) => subscriptions.includes(v.creator.id));
    const discovery = unwatched.filter((v) => !subscriptions.includes(v.creator.id));

    const subRecs = subscribed
      .sort((a, b) => new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime())
      .slice(0, 7)
      .map((v) => toRec(v, `From ${v.creator.name}`, "subscription"));

    const discoRecs = discovery
      .sort((a, b) => new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime())
      .slice(0, 3)
      .map((v) => toRec(v, `Discover ${v.creator.name}`, "discovery", 0.85));

    return [...subRecs, ...discoRecs];
  })();

  const featured = forYou[0]?.video ?? videos[0];

  // Continue watching
  const continueWatching: Recommendation[] = watchHistory
    .slice(-3)
    .reverse()
    .map((id) => videos.find((v) => v.id === id))
    .filter(Boolean)
    .map((video) => toRec(video!, "Continue watching", "subscription", 1));

  // Recently added
  const recentlyAdded: Recommendation[] = [...videos]
    .sort((a, b) => new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime())
    .slice(0, 10)
    .map((video) =>
      toRec(
        video,
        "",
        subscriptions.includes(video.creator.id) ? "subscription" : "discovery",
      ),
    );

  // Interviews
  const interviews: Recommendation[] = videos
    .filter((v) => v.category === "interview")
    .map((video) => toRec(video, "", "subscription", 0.8));

  return (
    <div className="pb-16">
      {featured && <HeroFeature video={featured} />}

      <div className="space-y-10 mt-8">
        <VideoRow
          title="For You"
          subtitle={`Based on your ${subscriptions.length} subscriptions`}
          recommendations={forYou}
          showReasons
          cardSize="lg"
        />

        {continueWatching.length > 0 && (
          <VideoRow title="Continue Watching" recommendations={continueWatching} />
        )}

        <VideoRow title="Recently Added" recommendations={recentlyAdded} />

        <VideoRow
          title="Deep Dives"
          subtitle="Long-form interviews and conversations"
          recommendations={interviews}
        />
      </div>
    </div>
  );
}

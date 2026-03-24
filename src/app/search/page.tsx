"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { searchVideos, videos } from "@/lib/mock-data";
import { SearchInput } from "@/components/search-input";
import { VideoCard } from "@/components/video-card";

function SearchResults() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const results = query ? searchVideos(query) : [];

  // Suggested topics for empty state
  const topics = ["AI", "music", "interview", "geopolitics", "mathematics", "creator economy"];

  return (
    <div className="pb-16 animate-fade-up">
      {/* Header */}
      <div className="px-8 pt-10 pb-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-display)] italic mb-6">
          Search
        </h1>
        <div className="max-w-2xl">
          <SearchInput defaultValue={query} autoFocus size="lg" />
        </div>
      </div>

      {/* Results or empty state */}
      <div className="px-8">
        {query ? (
          <>
            <p className="text-sm text-[var(--text-secondary)] mb-6">
              {results.length} result{results.length !== 1 ? "s" : ""} for &ldquo;
              <span className="text-[var(--accent)]">{query}</span>&rdquo;
            </p>

            {results.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5 stagger">
                {results.map((video) => (
                  <div key={video.id} className="animate-fade-up">
                    <VideoCard video={video} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-20 text-center">
                <p className="text-[var(--text-tertiary)]">No videos found. Try a different search.</p>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Suggested topics */}
            <div className="mb-8">
              <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                Popular Topics
              </h2>
              <div className="flex flex-wrap gap-2">
                {topics.map((topic) => (
                  <a
                    key={topic}
                    href={`/search?q=${encodeURIComponent(topic)}`}
                    className="px-4 py-2 text-sm text-[var(--text-secondary)] bg-[var(--bg-card)] border border-[var(--border-default)] rounded-full hover:border-[var(--accent)]/30 hover:text-[var(--accent)] transition-all"
                  >
                    {topic}
                  </a>
                ))}
              </div>
            </div>

            {/* All videos grid */}
            <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
              Browse All
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5 stagger">
              {videos.map((video) => (
                <div key={video.id} className="animate-fade-up">
                  <VideoCard video={video} />
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-[60vh]">
          <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}

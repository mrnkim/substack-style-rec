"use client";

import { useRef } from "react";
import type { Recommendation } from "@/lib/types";
import { VideoCard } from "./video-card";

interface VideoRowProps {
  title: string;
  subtitle?: string;
  recommendations: Recommendation[];
  showReasons?: boolean;
  cardSize?: "sm" | "md" | "lg";
}

export function VideoRow({
  title,
  subtitle,
  recommendations,
  showReasons = false,
  cardSize = "md",
}: VideoRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = direction === "left" ? -600 : 600;
    scrollRef.current.scrollBy({ left: amount, behavior: "smooth" });
  };

  if (recommendations.length === 0) return null;

  return (
    <section className="animate-fade-up">
      {/* Section header */}
      <div className="px-8 mb-3">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h2>
        {subtitle && (
          <p className="text-sm text-[var(--text-secondary)] mt-0.5">{subtitle}</p>
        )}
      </div>

      {/* Scrollable row with nav arrows */}
      <div className="relative group/row">
        {/* Left arrow */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-0 bottom-0 w-12 z-20 flex items-center justify-center bg-gradient-to-r from-[var(--bg-primary)] to-transparent opacity-0 group-hover/row:opacity-100 transition-opacity cursor-pointer"
          aria-label="Scroll left"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M12 4L6 10L12 16" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>

        {/* Cards */}
        <div ref={scrollRef} className="scroll-row stagger">
          {recommendations.map((rec) => (
            <VideoCard
              key={rec.video.id}
              video={rec.video}
              reason={showReasons ? rec.reason : undefined}
              matchedAttributes={showReasons ? rec.matchedAttributes : undefined}
              source={showReasons ? rec.source : undefined}
              size={cardSize}
            />
          ))}
        </div>

        {/* Right arrow */}
        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-0 bottom-0 w-12 z-20 flex items-center justify-center bg-gradient-to-l from-[var(--bg-primary)] to-transparent opacity-0 group-hover/row:opacity-100 transition-opacity cursor-pointer"
          aria-label="Scroll right"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M8 4L14 10L8 16" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </section>
  );
}

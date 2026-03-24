"use client";

import Link from "next/link";
import type { Creator } from "@/lib/types";
import { SubscribeButton } from "./subscribe-button";

interface CreatorCardProps {
  creator: Creator;
}

export function CreatorCard({ creator }: CreatorCardProps) {
  return (
    <Link
      href={`/creator/${creator.id}`}
      className="group block p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-default)] hover:border-[var(--accent)]/30 transition-all hover:-translate-y-1 hover:shadow-[var(--shadow-glow)]"
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center flex-shrink-0">
          <span className="text-lg font-bold text-[var(--text-tertiary)]">
            {creator.name[0]}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] truncate group-hover:text-[var(--accent)] transition-colors">
              {creator.name}
            </h3>
            <SubscribeButton creatorId={creator.id} size="sm" />
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">
            {creator.description}
          </p>
          <span className="text-[11px] text-[var(--text-tertiary)] mt-2 inline-block">
            {creator.videoCount} videos
          </span>
        </div>
      </div>
    </Link>
  );
}

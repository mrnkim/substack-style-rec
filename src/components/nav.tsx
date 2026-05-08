"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useUserState } from "@/lib/user-state";
import { getCreators, getVideos } from "@/lib/api";
import type { Creator, Video } from "@/lib/types";

type DropdownId = "subscriptions" | "history" | null;

export function Nav() {
  const pathname = usePathname();
  const { subscriptions, toggleSubscription, watchHistory, reset } = useUserState();
  const [creators, setCreators] = useState<Creator[]>([]);
  const [allVideos, setAllVideos] = useState<Video[]>([]);
  const [openDropdown, setOpenDropdown] = useState<DropdownId>(null);
  const subsRef = useRef<HTMLDivElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCreators().then(setCreators);
    getVideos().then(setAllVideos);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    if (!openDropdown) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        subsRef.current && !subsRef.current.contains(target) &&
        historyRef.current && !historyRef.current.contains(target)
      ) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [openDropdown]);

  const toggle = (id: DropdownId) => setOpenDropdown((prev) => (prev === id ? null : id));

  const subscribedCreators = creators.filter((c) => subscriptions.includes(c.id));
  const watchedVideos = watchHistory
    .slice()
    .reverse()
    .map((id) => allVideos.find((v) => v.id === id))
    .filter(Boolean) as Video[];

  const links = [
    { href: "/", label: "Home" },
    { href: "/explore", label: "Explore" },
    { href: "/search", label: "Search" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center px-8 bg-[var(--bg-primary)]/80 backdrop-blur-xl border-b border-[var(--border-light)]">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 mr-10 group">
        <div className="w-7 h-7 rounded-md bg-[var(--accent)] flex items-center justify-center transition-transform group-hover:scale-110">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M3 3L8 13L13 3" stroke="#1D1C1B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span className="text-sm font-semibold tracking-tight text-[var(--text-primary)]">
          CuratorAI
        </span>
      </Link>

      {/* Nav links */}
      <div className="flex items-center gap-1">
        {links.map((link) => {
          const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                isActive
                  ? "text-[var(--text-primary)] bg-[var(--bg-elevated)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        {/* Subscriptions dropdown */}
        <div className="relative" ref={subsRef}>
          <button
            onClick={() => toggle("subscriptions")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors cursor-pointer ${
              openDropdown === "subscriptions"
                ? "text-[var(--text-primary)] bg-[var(--bg-elevated)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <span>Subscriptions</span>
            {subscriptions.length > 0 && (
              <span className="ml-0.5 px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--accent)] text-[var(--text-inverse)] leading-none">
                {subscriptions.length}
              </span>
            )}
          </button>

          {openDropdown === "subscriptions" && (
            <div className="absolute right-0 top-full mt-2 w-72 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-[var(--shadow-elevated)] overflow-hidden animate-fade-up">
              <div className="px-4 py-2.5 border-b border-[var(--border-default)]">
                <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  Your Subscriptions
                </h3>
              </div>
              {subscribedCreators.length === 0 ? (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-[var(--text-tertiary)]">No subscriptions yet</p>
                  <Link
                    href="/explore"
                    onClick={() => setOpenDropdown(null)}
                    className="text-xs text-[var(--accent)] hover:underline mt-1 inline-block"
                  >
                    Explore creators
                  </Link>
                </div>
              ) : (
                <div className="max-h-64 overflow-y-auto">
                  {subscribedCreators.map((creator) => (
                    <div
                      key={creator.id}
                      className="flex items-center gap-3 px-4 py-2.5 hover:bg-[var(--bg-elevated)] transition-colors"
                    >
                      <Link
                        href={`/creator/${creator.id}`}
                        onClick={() => setOpenDropdown(null)}
                        className="flex items-center gap-3 flex-1 min-w-0"
                      >
                        <div className="w-8 h-8 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center shrink-0">
                          <span className="text-xs font-bold text-[var(--text-tertiary)]">
                            {creator.name[0]}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm text-[var(--text-primary)] truncate">{creator.name}</p>
                          <p className="text-[11px] text-[var(--text-tertiary)]">{creator.videoCount} videos</p>
                        </div>
                      </Link>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSubscription(creator.id);
                        }}
                        className="shrink-0 px-2 py-1 text-[10px] font-medium rounded border border-[var(--border-default)] text-[var(--text-secondary)] hover:border-[var(--error)] hover:text-[var(--error)] transition-colors cursor-pointer"
                      >
                        Unsubscribe
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Watch History dropdown */}
        <div className="relative" ref={historyRef}>
          <button
            onClick={() => toggle("history")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors cursor-pointer ${
              openDropdown === "history"
                ? "text-[var(--text-primary)] bg-[var(--bg-elevated)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span>History</span>
            {watchHistory.length > 0 && (
              <span className="ml-0.5 px-1.5 py-0.5 text-[10px] font-semibold rounded-full bg-[var(--bg-elevated)] text-[var(--text-primary)] leading-none border border-[var(--border-default)]">
                {watchHistory.length}
              </span>
            )}
          </button>

          {openDropdown === "history" && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-[var(--shadow-elevated)] overflow-hidden animate-fade-up">
              <div className="px-4 py-2.5 border-b border-[var(--border-default)] flex items-center justify-between">
                <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  Watch History
                </h3>
                {watchHistory.length > 0 && (
                  <button
                    onClick={reset}
                    className="text-[10px] font-medium text-[var(--text-tertiary)] hover:text-[var(--error)] transition-colors cursor-pointer"
                  >
                    Reset all
                  </button>
                )}
              </div>
              {watchedVideos.length === 0 ? (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-[var(--text-tertiary)]">No videos watched yet</p>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">Watch videos to get personalized recommendations</p>
                </div>
              ) : (
                <div className="max-h-72 overflow-y-auto">
                  {watchedVideos.map((video) => (
                    <Link
                      key={video.id}
                      href={`/watch/${video.id}`}
                      onClick={() => setOpenDropdown(null)}
                      className="flex items-center gap-3 px-4 py-2 hover:bg-[var(--bg-elevated)] transition-colors"
                    >
                      <div className="w-16 h-9 rounded overflow-hidden bg-[var(--bg-elevated)] shrink-0">
                        <img
                          src={video.thumbnailUrl}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs text-[var(--text-primary)] line-clamp-1">{video.title}</p>
                        <p className="text-[10px] text-[var(--text-tertiary)]">{video.creator.name}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* TwelveLabs badge */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)]">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
          <span className="text-xs font-medium text-[var(--accent)]">Powered by TwelveLabs + Pixeltable</span>
        </div>
      </div>
    </nav>
  );
}

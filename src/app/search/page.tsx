"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { getVideos, searchVideos, searchByFile } from "@/lib/api";
import type { SearchResult } from "@/lib/api";
import { VideoCard } from "@/components/video-card";
import { formatDuration } from "@/lib/utils";
import type { Video } from "@/lib/types";

const ACCEPT_TYPES = "image/jpeg,image/png,image/webp,video/mp4,video/webm,audio/mpeg,audio/mp4,audio/wav";

function modalityIcon(modality: string) {
  switch (modality) {
    case "image":
      return (
        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <rect x="1.5" y="2.5" width="13" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
          <circle cx="5.5" cy="6" r="1.5" stroke="currentColor" strokeWidth="1.2" />
          <path d="M1.5 11l3.5-4 3 3 2-2 4.5 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "video":
      return (
        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <rect x="1" y="3" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
          <path d="M11 6.5l4-2v7l-4-2V6.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
        </svg>
      );
    case "audio":
      return (
        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <path d="M8 1v14M4 4v8M12 4v8M1 6.5v3M15 6.5v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    default:
      return null;
  }
}

function getFileModality(file: File): string {
  if (file.type.startsWith("image/")) return "image";
  if (file.type.startsWith("video/")) return "video";
  if (file.type.startsWith("audio/")) return "audio";
  return "unknown";
}

function FilePreview({ file, onRemove }: { file: File; onRemove: () => void }) {
  const modality = getFileModality(file);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (modality === "image") {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [file, modality]);

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-[var(--bg-card)] border border-[var(--border-accent)] rounded-lg">
      <div className="flex items-center gap-2 text-[var(--accent)]">
        {modalityIcon(modality)}
        <span className="text-xs uppercase font-medium tracking-wider">{modality}</span>
      </div>
      {previewUrl && (
        <img src={previewUrl} alt="preview" className="w-10 h-10 rounded object-cover" />
      )}
      <span className="text-sm text-[var(--text-secondary)] truncate flex-1 max-w-[200px]">
        {file.name}
      </span>
      <span className="text-xs text-[var(--text-tertiary)]">
        {(file.size / 1024 / 1024).toFixed(1)} MB
      </span>
      <button
        onClick={onRemove}
        className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
        aria-label="Remove file"
      >
        <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

function SearchResults() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [textQuery, setTextQuery] = useState(query);
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [browseVideos, setBrowseVideos] = useState<Video[] | null>(null);
  const [searchLabel, setSearchLabel] = useState(query);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const doTextSearch = useCallback(async (q: string) => {
    setIsSearching(true);
    setSearchLabel(q);
    setSearchMessage(null);
    try {
      if (q) {
        const data = await searchVideos(q, { limit: 20 });
        setResults(data.results);
        setBrowseVideos(null);
      } else {
        const v = await getVideos();
        setBrowseVideos(v);
        setResults(null);
      }
    } finally {
      setIsSearching(false);
    }
  }, []);

  const doFileSearch = useCallback(async (file: File) => {
    setIsSearching(true);
    setSearchLabel(`Searching by ${getFileModality(file)}: ${file.name}`);
    setSearchMessage(null);
    try {
      const data = await searchByFile(file, { limit: 20 });
      setResults(data.results);
      setBrowseVideos(null);
      setSearchLabel(data.query || file.name);
      if (data.message) setSearchMessage(data.message);
    } finally {
      setIsSearching(false);
    }
  }, []);

  useEffect(() => {
    if (!uploadedFile) {
      doTextSearch(query);
    }
  }, [query, doTextSearch, uploadedFile]);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadedFile) return;
    const q = textQuery.trim();
    if (q) {
      window.history.pushState({}, "", `/search?q=${encodeURIComponent(q)}`);
      doTextSearch(q);
    }
  };

  const handleFileSelect = (file: File) => {
    setUploadedFile(file);
    setTextQuery("");
    doFileSearch(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
    e.target.value = "";
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setSearchLabel("");
    setResults(null);
    doTextSearch(query);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current++;
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) setIsDragging(false);
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  };

  const topics = ["AI", "music", "interview", "branding", "mathematics", "creator economy"];
  const videos = results ? results.map((r) => r.video) : browseVideos;
  const loading = videos === null && !isSearching;
  const hasQuery = !!query || !!uploadedFile;

  return (
    <div
      className="pb-16 animate-fade-up"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {isDragging && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4 p-12 border-2 border-dashed border-[var(--accent)] rounded-2xl bg-[var(--bg-card)]/80">
            <div className="text-[var(--accent)]">
              <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none">
                <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M20 16v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <p className="text-lg font-medium text-[var(--text-primary)]">Drop to search</p>
            <p className="text-sm text-[var(--text-secondary)]">Image, video clip, or audio file</p>
          </div>
        </div>
      )}

      <div className="px-8 pt-10 pb-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-2">
          Search
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mb-6">
          Search by text, or upload an image, video clip, or audio file for cross-modal search
        </p>

        {/* Search input row */}
        <div className="max-w-2xl">
          {uploadedFile ? (
            <FilePreview file={uploadedFile} onRemove={handleRemoveFile} />
          ) : (
            <form onSubmit={handleTextSubmit} className="relative">
              <div className="relative flex items-center gap-2">
                <div className="relative flex-1">
                  <svg
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] w-5 h-5"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M11 11L14.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                  <input
                    type="text"
                    value={textQuery}
                    onChange={(e) => setTextQuery(e.target.value)}
                    placeholder="Search videos by content..."
                    autoFocus
                    className="w-full bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] rounded-lg outline-none transition-all focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20 pl-11 pr-4 py-3 text-base"
                  />
                </div>

                {/* Upload buttons */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPT_TYPES}
                  onChange={handleFileInputChange}
                  className="hidden"
                />
                <div className="flex items-center gap-1">
                  {(["image", "video", "audio"] as const).map((mod) => (
                    <button
                      key={mod}
                      type="button"
                      onClick={() => {
                        if (fileInputRef.current) {
                          fileInputRef.current.accept =
                            mod === "image"
                              ? "image/jpeg,image/png,image/webp"
                              : mod === "video"
                                ? "video/mp4,video/webm"
                                : "audio/mpeg,audio/mp4,audio/wav";
                          fileInputRef.current.click();
                        }
                      }}
                      title={`Search by ${mod}`}
                      className="p-2.5 rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] text-[var(--text-tertiary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/30 transition-all"
                    >
                      {modalityIcon(mod)}
                    </button>
                  ))}
                </div>
              </div>
            </form>
          )}
        </div>
      </div>

      <div className="px-8">
        {/* Loading state */}
        {(loading || isSearching) && (
          <div className="flex items-center justify-center h-[40vh]">
            <div className="flex flex-col items-center gap-3">
              <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
              {isSearching && uploadedFile && (
                <p className="text-sm text-[var(--text-secondary)]">
                  Analyzing {getFileModality(uploadedFile)} with Marengo 3.0...
                </p>
              )}
            </div>
          </div>
        )}

        {/* Results */}
        {!loading && !isSearching && videos && hasQuery && (
          <>
            <p className="text-sm text-[var(--text-secondary)] mb-6">
              {videos.length} result{videos.length !== 1 ? "s" : ""} for{" "}
              {uploadedFile ? (
                <span className="text-[var(--accent)]">{searchLabel}</span>
              ) : (
                <>
                  &ldquo;<span className="text-[var(--accent)]">{searchLabel}</span>&rdquo;
                </>
              )}
            </p>
            {results && results.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5 stagger">
                {results.map((r, idx) => {
                  const hasScene = r.scene_start != null && r.scene_end != null;
                  const href = hasScene
                    ? `/watch/${r.video.id}?t=${Math.floor(r.scene_start!)}`
                    : `/watch/${r.video.id}`;
                  const thumbnail = r.scene_thumbnail_url || r.video.thumbnailUrl;
                  return (
                    <Link key={r.video.id} href={href} className="video-card block animate-fade-up group">
                      {/* Thumbnail */}
                      <div className="relative aspect-video rounded-lg overflow-hidden bg-[var(--bg-elevated)]">
                        <img
                          src={thumbnail}
                          alt={r.video.title}
                          className="absolute inset-0 w-full h-full object-cover"
                          loading="lazy"
                        />
                        {/* Rank badge */}
                        <span className="absolute top-2 left-2 w-6 h-6 flex items-center justify-center text-[11px] font-bold rounded-md bg-black/70 text-[var(--text-primary)]">
                          {idx + 1}
                        </span>
                        {/* Category pill — shown below with title */}
                        {/* Scene duration or total duration */}
                        <span className="absolute bottom-2 right-2 px-1.5 py-0.5 text-[10px] font-mono font-medium bg-black/70 text-[var(--text-primary)] rounded">
                          {hasScene
                            ? `${formatDuration(Math.floor(r.scene_start!))} – ${formatDuration(Math.floor(r.scene_end!))}`
                            : formatDuration(r.video.duration)}
                        </span>
                        {/* Play overlay */}
                        <div className="thumb-overlay rounded-lg">
                          <div className="w-10 h-10 rounded-full bg-[var(--accent)] flex items-center justify-center shadow-lg">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                              <path d="M4 2L14 8L4 14V2Z" fill="#1D1C1B" />
                            </svg>
                          </div>
                        </div>
                      </div>
                      {/* Info */}
                      <div className="mt-2.5 space-y-1">
                        <div className="flex items-start gap-1.5">
                          <h3 className="text-sm font-medium text-[var(--text-primary)] leading-snug line-clamp-2 group-hover:text-[var(--accent)] transition-colors flex-1">
                            {r.video.title}
                          </h3>
                          <span className={`shrink-0 mt-0.5 px-2 py-0.5 text-[10px] font-medium rounded-full pill-${r.video.category}`}>
                            {r.video.category}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-4 h-4 rounded-full bg-[var(--bg-elevated)] flex items-center justify-center">
                            <span className="text-[8px] font-bold text-[var(--text-tertiary)]">
                              {r.video.creator.name[0]}
                            </span>
                          </div>
                          <span className="text-xs text-[var(--text-secondary)]">{r.video.creator.name}</span>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="py-20 text-center">
                <p className="text-[var(--text-tertiary)]">
                  {searchMessage || "No videos found. Try a different search."}
                </p>
              </div>
            )}
          </>
        )}

        {/* Empty state: topic pills + browse all */}
        {!loading && !isSearching && videos && !hasQuery && (
          <>
            {/* Multimodal hint */}
            <div className="mb-8 p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <span className="text-[var(--accent)]">
                  <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
                    <path d="M8 1l2 5h5l-4 3 1.5 5L8 11l-4.5 3L5 9 1 6h5l2-5z" fill="currentColor" />
                  </svg>
                </span>
                Cross-Modal Search
              </h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Upload an image, short video clip, or audio file to find videos with matching content.
                Powered by Twelve Labs Marengo 3.0 + Pixeltable scene detection — all modalities share the same embedding space.
              </p>
            </div>

            <div className="mb-8">
              <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                Popular Topics
              </h2>
              <div className="flex flex-wrap gap-2">
                {topics.map((topic) => (
                  <button
                    key={topic}
                    onClick={() => {
                      setTextQuery(topic);
                      window.history.pushState({}, "", `/search?q=${encodeURIComponent(topic)}`);
                      doTextSearch(topic);
                    }}
                    className="px-4 py-2 text-sm text-[var(--text-secondary)] bg-[var(--bg-card)] border border-[var(--border-default)] rounded-full hover:border-[var(--accent)]/30 hover:text-[var(--accent)] transition-all"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>

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

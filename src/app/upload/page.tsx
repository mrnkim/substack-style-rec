"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadVideo } from "@/lib/api";

const CATEGORIES = ["interview", "commentary", "creative", "educational"] as const;
const MAX_SIZE_MB = 100;

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<string>("interview");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const handleFileSelect = useCallback((f: File) => {
    setError(null);
    if (!f.type.startsWith("video/")) {
      setError("Only video files (mp4, webm, mov) are accepted.");
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum ${MAX_SIZE_MB}MB.`);
      return;
    }
    setFile(f);
    if (!title) {
      setTitle(f.name.replace(/\.[^.]+$/, ""));
    }
  }, [title]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title.trim()) return;

    setIsUploading(true);
    setError(null);
    try {
      const result = await uploadVideo(file, title.trim(), category);
      if (result) {
        setSuccess(`"${result.title}" uploaded. Pixeltable is processing scene detection and embeddings.`);
        setFile(null);
        setTitle("");
        setTimeout(() => router.push("/search"), 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
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
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFileSelect(f);
  };

  return (
    <div className="pb-16 animate-fade-up px-8 pt-10 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-[var(--text-primary)] font-[family-name:var(--font-brand)] mb-2">
        Upload Video
      </h1>
      <p className="text-sm text-[var(--text-secondary)] mb-8">
        Add your own video. Pixeltable will automatically detect scenes, generate embeddings,
        and extract attributes so it appears in search and recommendations.
      </p>

      {success && (
        <div className="mb-6 p-4 rounded-lg bg-[var(--accent-muted)] border border-[var(--border-accent)]">
          <p className="text-sm text-[var(--accent)]">{success}</p>
          <p className="text-xs text-[var(--text-tertiary)] mt-1">Redirecting to search...</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Drop zone */}
        <div
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-all ${
            isDragging
              ? "border-[var(--accent)] bg-[var(--accent-muted)]"
              : file
                ? "border-[var(--border-accent)] bg-[var(--bg-card)]"
                : "border-[var(--border-default)] bg-[var(--bg-card)] hover:border-[var(--accent)]/40"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/webm,video/quicktime"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFileSelect(f);
              e.target.value = "";
            }}
            className="hidden"
          />

          {file ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-2 text-[var(--accent)]">
                <svg className="w-5 h-5" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="3" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
                  <path d="M11 6.5l4-2v7l-4-2V6.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
                </svg>
                <span className="font-medium">{file.name}</span>
              </div>
              <p className="text-xs text-[var(--text-tertiary)]">
                {(file.size / 1024 / 1024).toFixed(1)} MB
              </p>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] underline"
              >
                Change file
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-[var(--text-tertiary)]">
                <svg className="w-10 h-10 mx-auto" viewBox="0 0 24 24" fill="none">
                  <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M20 16v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                Drop a video file here, or click to browse
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">
                MP4, WebM, or MOV. Max {MAX_SIZE_MB}MB.
              </p>
            </div>
          )}
        </div>

        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Video title"
            required
            className="w-full bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] rounded-lg px-4 py-3 text-base outline-none transition-all focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20"
          />
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            Category
          </label>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={`px-4 py-2 text-sm rounded-full border transition-all ${
                  category === cat
                    ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-muted)]"
                    : "border-[var(--border-default)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!file || !title.trim() || isUploading}
          className="w-full py-3 px-6 rounded-lg font-medium text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-[var(--accent)] text-black hover:brightness-110"
        >
          {isUploading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              Uploading...
            </span>
          ) : (
            "Upload Video"
          )}
        </button>

        <p className="text-xs text-[var(--text-tertiary)] text-center">
          After upload, Pixeltable runs scene detection + Marengo 3.0 embedding automatically.
          The video will appear in search results within a few minutes.
        </p>
      </form>
    </div>
  );
}

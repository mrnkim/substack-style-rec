/**
 * Client-side API helpers.
 *
 * Switch API_BASE to toggle between:
 *   "/api"                        — Next.js API routes (Twelve Labs direct)
 *   "http://localhost:8000/api"   — PixelTable FastAPI backend
 */

import type { Video, Creator, Recommendation } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "/api";

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------

export async function getVideos(opts?: {
  category?: string;
  creatorId?: string;
}): Promise<Video[]> {
  const params = new URLSearchParams();
  if (opts?.category) params.set("category", opts.category);
  if (opts?.creatorId) params.set("creator_id", opts.creatorId);

  const qs = params.toString();
  const res = await fetch(`${API_BASE}/videos${qs ? `?${qs}` : ""}`);
  const data = await res.json();
  return data.data;
}

export async function getVideo(id: string): Promise<Video | null> {
  const res = await fetch(`${API_BASE}/videos/${id}`);
  if (!res.ok) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Creators
// ---------------------------------------------------------------------------

export async function getCreators(): Promise<Creator[]> {
  const res = await fetch(`${API_BASE}/creators`);
  const data = await res.json();
  return data.data;
}

export async function getCreator(
  id: string,
): Promise<{ creator: Creator; videos: Video[] } | null> {
  const res = await fetch(`${API_BASE}/creators/${id}`);
  if (!res.ok) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Recommendations (PixelTable backend only)
// ---------------------------------------------------------------------------

export async function getForYouRecommendations(
  subscriptions: string[],
  watchHistory: string[],
  limit = 10,
): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/recommendations/for-you`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subscriptions, watchHistory, limit }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.recommendations;
}

export async function getSimilarVideos(
  videoId: string,
  watchHistory: string[],
  limit = 6,
): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/recommendations/similar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ videoId, watchHistory, limit }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.recommendations;
}

export async function getCreatorCatalog(
  creatorId: string,
  watchHistory: string[],
  limit = 20,
): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/recommendations/creator-catalog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ creatorId, watchHistory, limit }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.recommended ?? data.recommendations ?? [];
}

// ---------------------------------------------------------------------------
// Search (PixelTable backend only)
// ---------------------------------------------------------------------------

export async function searchVideos(
  query: string,
  opts?: { creatorId?: string; limit?: number },
): Promise<{ query: string; results: { video: Video; score: number }[] }> {
  const params = new URLSearchParams({ q: query });
  if (opts?.creatorId) params.set("creator_id", opts.creatorId);
  if (opts?.limit) params.set("limit", String(opts.limit));

  const res = await fetch(`${API_BASE}/search?${params}`);
  if (!res.ok) return { query, results: [] };
  return res.json();
}

/**
 * Client-side API helpers.
 *
 * Switch API_BASE to toggle between:
 *   "/api"                        — Next.js API routes (Twelve Labs direct)
 *   "http://localhost:8000/api"   — Pixeltable FastAPI backend
 */

import type { Video, Creator, Recommendation } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------

export async function getVideos(opts?: {
  category?: string;
  creatorId?: string;
}): Promise<Video[]> {
  try {
    const params = new URLSearchParams();
    if (opts?.category) params.set("category", opts.category);
    if (opts?.creatorId) params.set("creator_id", opts.creatorId);
    const qs = params.toString();
    const res = await fetch(`${API_BASE}/videos${qs ? `?${qs}` : ""}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.data ?? [];
  } catch {
    return [];
  }
}

export async function getVideo(id: string): Promise<Video | null> {
  try {
    const res = await fetch(`${API_BASE}/videos/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Creators
// ---------------------------------------------------------------------------

export async function getCreators(): Promise<Creator[]> {
  try {
    const res = await fetch(`${API_BASE}/creators`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.data ?? [];
  } catch {
    return [];
  }
}

export async function getCreator(
  id: string,
): Promise<{ creator: Creator; videos: Video[] } | null> {
  try {
    const res = await fetch(`${API_BASE}/creators/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------------

export async function getForYouRecommendations(
  subscriptions: string[],
  watchHistory: string[],
  limit = 10,
): Promise<Recommendation[]> {
  try {
    const res = await fetch(`${API_BASE}/recommendations/for-you`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subscriptions, watchHistory, limit }),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.recommendations ?? [];
  } catch {
    return [];
  }
}

export async function getSimilarVideos(
  videoId: string,
  watchHistory: string[],
  limit = 6,
): Promise<Recommendation[]> {
  try {
    const res = await fetch(`${API_BASE}/recommendations/similar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ videoId, watchHistory, limit }),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.recommendations ?? [];
  } catch {
    return [];
  }
}

export async function getCreatorCatalog(
  creatorId: string,
  watchHistory: string[],
  limit = 20,
): Promise<Recommendation[]> {
  try {
    const res = await fetch(`${API_BASE}/recommendations/creator-catalog`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ creatorId, watchHistory, limit }),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.recommended ?? data.recommendations ?? [];
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export type SearchResult = { video: Video; score: number };
export type SearchApiResponse = { query: string; modality?: string; results: SearchResult[]; message?: string };

export async function searchVideos(
  query: string,
  opts?: { creatorId?: string; limit?: number },
): Promise<SearchApiResponse> {
  try {
    const params = new URLSearchParams({ q: query });
    if (opts?.creatorId) params.set("creator_id", opts.creatorId);
    if (opts?.limit) params.set("limit", String(opts.limit));
    const res = await fetch(`${API_BASE}/search?${params}`);
    if (!res.ok) return { query, results: [] };
    return res.json();
  } catch {
    return { query, results: [] };
  }
}

/**
 * Multimodal search: upload an image, video clip, or audio file to find
 * matching videos via Marengo 3.0 cross-modal embeddings.
 */
export async function searchByFile(
  file: File,
  opts?: { query?: string; limit?: number },
): Promise<SearchApiResponse> {
  try {
    const form = new FormData();
    form.append("file", file);
    if (opts?.query) form.append("q", opts.query);
    form.append("limit", String(opts?.limit ?? 10));

    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) return { query: file.name, results: [] };
    return res.json();
  } catch {
    return { query: file.name, results: [] };
  }
}

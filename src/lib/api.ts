/**
 * Client-side API helpers.
 *
 * Switch API_BASE to toggle between:
 *   "/api"                        — Next.js API routes (Twelve Labs direct)
 *   "http://localhost:8000/api"   — Pixeltable FastAPI backend
 */

import type { Video, Creator, Recommendation } from "./types";
import { withCache } from "./request-cache";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

// Pixeltable's videos.insert(..., on_error="ignore") doesn't collapse
// primary-key collisions across re-runs, so the table can carry duplicate
// rows from earlier setup attempts. Dedupe at the API boundary so the UI
// never renders the same id twice.
function dedupeById<T extends { id: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const it of items) {
    if (!it?.id || seen.has(it.id)) continue;
    seen.add(it.id);
    out.push(it);
  }
  return out;
}

function dedupeRecs(items: Recommendation[]): Recommendation[] {
  const seen = new Set<string>();
  const out: Recommendation[] = [];
  for (const it of items) {
    const id = it?.video?.id;
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push(it);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------

export async function getVideos(opts?: {
  category?: string;
  creatorId?: string;
}): Promise<Video[]> {
  const key = `videos:${opts?.category ?? ""}:${opts?.creatorId ?? ""}`;
  return withCache(key, async () => {
    try {
      const params = new URLSearchParams();
      if (opts?.category) params.set("category", opts.category);
      if (opts?.creatorId) params.set("creator_id", opts.creatorId);
      const qs = params.toString();
      const res = await fetch(`${API_BASE}/videos${qs ? `?${qs}` : ""}`);
      if (!res.ok) return [];
      const data = await res.json();
      return dedupeById((data.data ?? []) as Video[]);
    } catch {
      return [];
    }
  });
}

export async function getVideo(id: string): Promise<Video | null> {
  return withCache(`video:${id}`, async () => {
    try {
      const res = await fetch(`${API_BASE}/videos/${id}`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  });
}

// ---------------------------------------------------------------------------
// Creators
// ---------------------------------------------------------------------------

export async function getCreators(): Promise<Creator[]> {
  return withCache("creators", async () => {
    try {
      const res = await fetch(`${API_BASE}/creators`);
      if (!res.ok) return [];
      const data = await res.json();
      return dedupeById((data.data ?? []) as Creator[]);
    } catch {
      return [];
    }
  });
}

export async function getCreator(
  id: string,
): Promise<{ creator: Creator; videos: Video[] } | null> {
  return withCache(`creator:${id}`, async () => {
    try {
      const res = await fetch(`${API_BASE}/creators/${id}`);
      if (!res.ok) return null;
      const data = await res.json();
      if (data?.videos) data.videos = dedupeById(data.videos as Video[]);
      return data;
    } catch {
      return null;
    }
  });
}

// ---------------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------------

export async function getForYouRecommendations(
  subscriptions: string[],
  watchHistory: string[],
  limit = 10,
): Promise<Recommendation[]> {
  // Sort key components so toggling a subscription / marking a video watched
  // produces a new key (fresh fetch) without serving a stale feed.
  const key = `foryou:${[...subscriptions].sort().join(",")}:${[...watchHistory].sort().join(",")}:${limit}`;
  return withCache(key, async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/for-you`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subscriptions, watchHistory, limit }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      return dedupeRecs((data.recommendations ?? []) as Recommendation[]);
    } catch {
      return [];
    }
  });
}

export async function getSimilarVideos(
  videoId: string,
  watchHistory: string[],
  limit = 6,
): Promise<Recommendation[]> {
  const key = `similar:${videoId}:${[...watchHistory].sort().join(",")}:${limit}`;
  return withCache(key, async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/similar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ videoId, watchHistory, limit }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      return dedupeRecs((data.recommendations ?? []) as Recommendation[]);
    } catch {
      return [];
    }
  });
}

export async function getCreatorCatalog(
  creatorId: string,
  watchHistory: string[],
  limit = 20,
): Promise<Recommendation[]> {
  const key = `catalog:${creatorId}:${[...watchHistory].sort().join(",")}:${limit}`;
  return withCache(key, async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/creator-catalog`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ creatorId, watchHistory, limit }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      const recs = (data.recommended ?? data.recommendations ?? []) as Recommendation[];
      return dedupeRecs(recs);
    } catch {
      return [];
    }
  });
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
  const key = `search:${query}:${opts?.creatorId ?? ""}:${opts?.limit ?? ""}`;
  // Shorter TTL: search queries are more varied and less worth holding long.
  return withCache(
    key,
    async () => {
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
    },
    60_000,
  );
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

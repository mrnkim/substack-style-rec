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
// In-memory cache
//
// Keeps already-fetched videos and recommendations available with no network
// round-trip on revisit. Lives for the lifetime of the SPA tab; cleared by a
// hard refresh. TTL guards against truly stale data on long-lived sessions.
// Coalesces concurrent requests for the same key (in-flight Promise reuse).
// ---------------------------------------------------------------------------

type CacheEntry<T> = { value: T; expires: number };
const TTL_MS = 5 * 60 * 1000;

const cache = new Map<string, CacheEntry<unknown>>();
const inflight = new Map<string, Promise<unknown>>();

function cached<T>(key: string, ttl: number, fetcher: () => Promise<T>): Promise<T> {
  const now = Date.now();
  const hit = cache.get(key) as CacheEntry<T> | undefined;
  if (hit && hit.expires > now) return Promise.resolve(hit.value);

  const pending = inflight.get(key) as Promise<T> | undefined;
  if (pending) return pending;

  const promise = fetcher()
    .then((value) => {
      cache.set(key, { value, expires: Date.now() + ttl });
      return value;
    })
    .finally(() => {
      inflight.delete(key);
    });
  inflight.set(key, promise);
  return promise;
}

export function clearApiCache(prefix?: string) {
  if (!prefix) {
    cache.clear();
    return;
  }
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------

// Dedupe a list keeping the first occurrence of each `id`.
// Pixeltable's `videos.insert(..., on_error="ignore")` does not actually
// drop primary-key collisions the way we expected, so the deployed table
// can carry stale duplicate rows from earlier setup runs. Until the
// production DB is freshly repopulated, dedupe at the API boundary so the
// UI never shows the same video twice.
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

export async function getVideos(opts?: {
  category?: string;
  creatorId?: string;
}): Promise<Video[]> {
  const key = `videos:${opts?.category ?? ""}:${opts?.creatorId ?? ""}`;
  return cached(key, TTL_MS, async () => {
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
  return cached(`video:${id}`, TTL_MS, async () => {
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
  return cached("creators:all", TTL_MS, async () => {
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
  try {
    const res = await fetch(`${API_BASE}/creators/${id}`);
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.videos) data.videos = dedupeById(data.videos as Video[]);
    return data;
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
  // Key on full inputs — for-you results genuinely change as the user
  // subscribes/watches, so different states should not share a cache slot.
  const key = `for-you:${[...subscriptions].sort().join(",")}|${[...watchHistory].sort().join(",")}|${limit}`;
  return cached(key, TTL_MS, async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/for-you`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subscriptions, watchHistory, limit }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      const recs = (data.recommendations ?? []) as Recommendation[];
      console.group("%c[For You] %d recommendations", "color:#00DC82;font-weight:bold", recs.length);
      recs.forEach((r, i) =>
        console.log(`#${i + 1} [${r.source}] score=${r.score?.toFixed(4) ?? "N/A"} | ${r.video.creator.name} — ${r.video.title}`)
      );
      console.groupEnd();
      return recs;
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
  // Key on videoId + limit only. watchHistory shifts as the user watches,
  // but the similarity-based ranking for a given video is essentially stable
  // across small history changes — caching by id keeps revisits instant.
  const key = `similar:${videoId}|${limit}`;
  return cached(key, TTL_MS, async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/similar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ videoId, watchHistory, limit }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      const recs = (data.recommendations ?? []) as Recommendation[];
      console.group("%c[Similar] %d recommendations", "color:#6CD5FD;font-weight:bold", recs.length);
      recs.forEach((r, i) =>
        console.log(`#${i + 1} [${r.source}] score=${r.score?.toFixed(4) ?? "N/A"} | ${r.video.creator.name} — ${r.video.title}`)
      );
      console.groupEnd();
      return recs;
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

export type SearchResult = { video: Video; score: number; scene_start?: number; scene_end?: number; scene_thumbnail_url?: string };
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

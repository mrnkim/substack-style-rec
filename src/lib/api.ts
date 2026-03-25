/**
 * Client-side API helpers.
 * Currently calls Next.js API routes → Twelve Labs.
 * When PixelTable backend is ready, swap the base URL.
 */

import type { Video, Creator } from "./types";

const API_BASE = "/api";

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

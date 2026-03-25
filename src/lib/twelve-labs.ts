/**
 * Server-side Twelve Labs API client.
 * Fetches videos from TL index and maps to our Video type.
 * user_metadata contains: youtubeId, creatorId, creatorName, category, uploadDate
 */

import type { Video, VideoAttributes, Creator } from "./types";

const API_KEY = process.env.TWELVELABS_API_KEY!;
const INDEX_ID = process.env.TWELVELABS_INDEX_ID!;
const BASE_URL = "https://api.twelvelabs.io/v1.3";

// Creator descriptions (not stored in TL — static enrichment)
const CREATOR_DESCRIPTIONS: Record<string, string> = {
  "UCPD_bxCRGpmmeQcbe2kpPaA": "Home of Hot Ones and the best food content on the internet.",
  "UC-b3c7kxa5vU-bnmaROgvog": "Business strategy, branding, and design education for creative professionals.",
  "UCamLstJyCa-t5gfZegxsFMw": "Exploring the creator economy through interviews and deep analysis of digital media.",
  "UCGq-a57w-aPwyi3pW7XLiHw": "Steven Bartlett hosts unfiltered conversations with the world's most influential people.",
  "UCmGSJVG3mCRXVOP4yZrU1Dw": "Visual storytelling that explains how borders, power, and money shape our world.",
  "UC4QZ_LsYcvcq7qOsOhpAX4A": "Exploring the stories behind technology, business, and the ideas shaping our future.",
  "UCLXo7UDZvByw2ixzpQCufnA": "Vox Earworm — the music that defines culture and why certain songs stick.",
  "UCDsElQQt_gCZ9LgnW-7v-cQ": "Fair Companies — self-sufficient living, tiny homes, and sustainable architecture worldwide.",
  "UCYO_jab_esuFRV4b17AJtAw": "Animated math — making complex ideas feel intuitive through visual storytelling.",
  "UCk2U-Oqn7RXf-ydPqfSxG5g": "Practical science-backed advice on motivation, habits, and personal transformation.",
  "UCBv7HEHuVlNAELGi5XJd85Q": "Exclusive artist interviews, live sessions, and music documentaries.",
};

interface TLVideo {
  _id: string;
  system_metadata: {
    duration: number;
    filename: string;
  };
  hls?: {
    video_url: string;
    thumbnail_urls: string[];
    status: string;
  };
  user_metadata?: {
    youtubeId?: string;
    creatorId?: string;
    creatorName?: string;
    category?: string;
    uploadDate?: string;
    topic?: string[];
    style?: string;
    tone?: string;
  };
}

interface TLListResponse {
  data: TLVideo[];
  page_info: {
    page: number;
    total_page: number;
    total_results: number;
  };
}

function stripExtension(filename: string): string {
  return filename.replace(/\.(mp4|webm|mkv|mov)$/i, "").trim();
}

function mapTLVideoToVideo(tlv: TLVideo): Video | null {
  const meta = tlv.user_metadata;
  if (!meta?.creatorId || !meta?.creatorName) return null;

  const creator: Creator = {
    id: meta.creatorId,
    name: meta.creatorName,
    avatarUrl: "",
    description: CREATOR_DESCRIPTIONS[meta.creatorId] ?? "",
    videoCount: 0, // filled in by caller
  };

  const video: Video = {
    id: tlv._id,
    title: stripExtension(tlv.system_metadata.filename),
    creator,
    category: (meta.category as Video["category"]) ?? "interview",
    duration: Math.round(tlv.system_metadata.duration),
    thumbnailUrl: tlv.hls?.thumbnail_urls?.[0] ?? "",
    hlsUrl: tlv.hls?.video_url,
    uploadDate: meta.uploadDate ?? "",
  };

  // Attach attributes if available (from Analyze API, stored in user_metadata)
  if (meta.topic || meta.style || meta.tone) {
    video.attributes = {
      topic: meta.topic ?? [],
      style: (meta.style ?? "interview") as VideoAttributes["style"],
      tone: (meta.tone ?? "serious") as VideoAttributes["tone"],
    };
  }

  return video;
}

async function tlFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "x-api-key": API_KEY },
    next: { revalidate: 300 }, // cache 5 min
  });
  if (!res.ok) {
    throw new Error(`Twelve Labs API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAllVideos(): Promise<Video[]> {
  const videos: Video[] = [];
  let page = 1;

  while (true) {
    const resp = await tlFetch<TLListResponse>(
      `/indexes/${INDEX_ID}/videos?page=${page}&page_limit=50`,
    );
    for (const tlv of resp.data) {
      const v = mapTLVideoToVideo(tlv);
      if (v) videos.push(v);
    }
    if (page >= resp.page_info.total_page) break;
    page++;
  }

  // Fill in videoCount per creator
  const creatorCounts = new Map<string, number>();
  for (const v of videos) {
    creatorCounts.set(v.creator.id, (creatorCounts.get(v.creator.id) ?? 0) + 1);
  }
  for (const v of videos) {
    v.creator.videoCount = creatorCounts.get(v.creator.id) ?? 0;
  }

  return videos;
}

export async function fetchVideoById(videoId: string): Promise<Video | null> {
  try {
    const tlv = await tlFetch<TLVideo>(`/indexes/${INDEX_ID}/videos/${videoId}`);
    return mapTLVideoToVideo(tlv);
  } catch {
    return null;
  }
}

export async function fetchCreators(): Promise<Creator[]> {
  const videos = await fetchAllVideos();
  const creatorMap = new Map<string, Creator>();
  for (const v of videos) {
    if (!creatorMap.has(v.creator.id)) {
      creatorMap.set(v.creator.id, { ...v.creator });
    }
  }
  return Array.from(creatorMap.values());
}

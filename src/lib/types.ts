export interface Creator {
  id: string;
  name: string;
  avatarUrl: string;
  description: string;
  videoCount: number;
}

export type VideoStyle =
  | "interview"
  | "documentary"
  | "essay"
  | "tutorial"
  | "conversation"
  | "analysis"
  | "performance"
  | "explainer";

export type VideoTone =
  | "serious"
  | "casual"
  | "playful"
  | "contemplative"
  | "energetic"
  | "analytical";

export interface VideoAttributes {
  topic: string[];
  style: VideoStyle;
  tone: VideoTone;
}

export interface Video {
  id: string;
  title: string;
  creator: Creator;
  category: "interview" | "commentary" | "creative" | "educational";
  duration: number;
  thumbnailGradient: string;
  uploadDate: string;
  attributes: VideoAttributes;
}

export interface Recommendation {
  video: Video;
  score: number;
  reason: string;
  matchedAttributes: string[];
  source: "subscription" | "discovery";
}

export interface UserState {
  subscriptions: string[];
  watchHistory: string[];
}

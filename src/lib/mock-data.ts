import { Creator, Video, Recommendation } from "./types";

// ── Creators ────────────────────────────────────────────────────────────────

export const creators: Creator[] = [
  {
    id: "lex",
    name: "Lex Fridman",
    avatarUrl: "",
    description: "Long-form conversations about AI, science, philosophy, and the nature of intelligence.",
    videoCount: 4,
  },
  {
    id: "colin-samir",
    name: "Colin and Samir",
    avatarUrl: "",
    description: "Exploring the creator economy through interviews and deep analysis of digital media.",
    videoCount: 3,
  },
  {
    id: "diary-ceo",
    name: "The Diary of a CEO",
    avatarUrl: "",
    description: "Steven Bartlett hosts unfiltered conversations with the world's most influential people.",
    videoCount: 3,
  },
  {
    id: "johnny-harris",
    name: "Johnny Harris",
    avatarUrl: "",
    description: "Visual storytelling that explains how borders, power, and money shape our world.",
    videoCount: 3,
  },
  {
    id: "coldfusion",
    name: "ColdFusion",
    avatarUrl: "",
    description: "Exploring the stories behind technology, business, and the ideas shaping our future.",
    videoCount: 3,
  },
  {
    id: "vox-earworm",
    name: "Vox Earworm",
    avatarUrl: "",
    description: "The music that defines culture — why certain songs stick and what they reveal about us.",
    videoCount: 3,
  },
  {
    id: "kirsten-dirksen",
    name: "Kirsten Dirksen",
    avatarUrl: "",
    description: "Fair Companies — self-sufficient living, tiny homes, and sustainable architecture worldwide.",
    videoCount: 2,
  },
  {
    id: "3blue1brown",
    name: "3Blue1Brown",
    avatarUrl: "",
    description: "Animated math — making complex ideas feel intuitive through visual storytelling.",
    videoCount: 3,
  },
];

// ── Gradient palette (category-based) ────────────────────────────────────────

const gradients = {
  interview: [
    "linear-gradient(135deg, #1a0a00 0%, #4a1a08 40%, #8b3a1a 100%)",
    "linear-gradient(135deg, #0a0a1a 0%, #1a2a4a 40%, #3a4a6a 100%)",
    "linear-gradient(135deg, #1a0a0a 0%, #3a1a2a 40%, #5a2a3a 100%)",
    "linear-gradient(135deg, #0a1a0a 0%, #1a3a2a 40%, #2a5a3a 100%)",
  ],
  commentary: [
    "linear-gradient(135deg, #0a0a1a 0%, #0a2a4a 40%, #1a4a7a 100%)",
    "linear-gradient(135deg, #0a1a1a 0%, #1a3a3a 40%, #2a5a5a 100%)",
    "linear-gradient(135deg, #1a0a1a 0%, #2a1a3a 40%, #4a2a5a 100%)",
  ],
  creative: [
    "linear-gradient(135deg, #1a0a1a 0%, #3a1a4a 40%, #6a2a7a 100%)",
    "linear-gradient(135deg, #1a1a0a 0%, #3a3a1a 40%, #5a5a2a 100%)",
    "linear-gradient(135deg, #0a1a1a 0%, #1a4a3a 40%, #2a6a5a 100%)",
  ],
  educational: [
    "linear-gradient(135deg, #001a0a 0%, #003a2a 40%, #005a3a 100%)",
    "linear-gradient(135deg, #0a0a1a 0%, #1a2a3a 40%, #2a3a5a 100%)",
    "linear-gradient(135deg, #0a1a0a 0%, #2a3a1a 40%, #3a5a2a 100%)",
  ],
};

function getGradient(category: string, index: number): string {
  const palette = gradients[category as keyof typeof gradients] || gradients.interview;
  return palette[index % palette.length];
}

// ── Videos ───────────────────────────────────────────────────────────────────

const creatorMap = Object.fromEntries(creators.map((c) => [c.id, c]));

export const videos: Video[] = [
  // Lex Fridman — Interview (4)
  {
    id: "v-lex-01",
    title: "The Future of AI and Human Consciousness",
    creator: creatorMap["lex"],
    category: "interview",
    duration: 7320,
    thumbnailGradient: getGradient("interview", 0),
    uploadDate: "2025-09-12",
    attributes: { topic: ["AI", "consciousness", "philosophy"], style: "interview", tone: "serious" },
  },
  {
    id: "v-lex-02",
    title: "Quantum Computing and the Limits of Knowledge",
    creator: creatorMap["lex"],
    category: "interview",
    duration: 5460,
    thumbnailGradient: getGradient("interview", 1),
    uploadDate: "2025-07-28",
    attributes: { topic: ["quantum computing", "physics", "science"], style: "interview", tone: "serious" },
  },
  {
    id: "v-lex-03",
    title: "Robotics, War, and the Future of Humanity",
    creator: creatorMap["lex"],
    category: "interview",
    duration: 6180,
    thumbnailGradient: getGradient("interview", 2),
    uploadDate: "2025-05-14",
    attributes: { topic: ["robotics", "military", "ethics"], style: "interview", tone: "serious" },
  },
  {
    id: "v-lex-04",
    title: "Language, Thought, and the Nature of Intelligence",
    creator: creatorMap["lex"],
    category: "interview",
    duration: 8100,
    thumbnailGradient: getGradient("interview", 3),
    uploadDate: "2025-03-02",
    attributes: { topic: ["linguistics", "AI", "cognition"], style: "interview", tone: "contemplative" },
  },

  // Colin and Samir — Interview (3)
  {
    id: "v-cs-01",
    title: "How MrBeast Built a Media Empire",
    creator: creatorMap["colin-samir"],
    category: "interview",
    duration: 2340,
    thumbnailGradient: getGradient("interview", 1),
    uploadDate: "2025-10-05",
    attributes: { topic: ["creator economy", "media", "business"], style: "interview", tone: "energetic" },
  },
  {
    id: "v-cs-02",
    title: "The Economics of YouTube in 2025",
    creator: creatorMap["colin-samir"],
    category: "interview",
    duration: 1920,
    thumbnailGradient: getGradient("interview", 2),
    uploadDate: "2025-08-18",
    attributes: { topic: ["YouTube", "monetization", "creator economy"], style: "analysis", tone: "analytical" },
  },
  {
    id: "v-cs-03",
    title: "Why Every Creator Needs a Media Strategy",
    creator: creatorMap["colin-samir"],
    category: "interview",
    duration: 2100,
    thumbnailGradient: getGradient("interview", 3),
    uploadDate: "2025-06-22",
    attributes: { topic: ["media strategy", "content creation", "growth"], style: "conversation", tone: "energetic" },
  },

  // Diary of a CEO — Interview (3)
  {
    id: "v-dceo-01",
    title: "The Psychology of Self-Sabotage",
    creator: creatorMap["diary-ceo"],
    category: "interview",
    duration: 5400,
    thumbnailGradient: getGradient("interview", 0),
    uploadDate: "2025-11-01",
    attributes: { topic: ["psychology", "self-improvement", "behavior"], style: "interview", tone: "contemplative" },
  },
  {
    id: "v-dceo-02",
    title: "AI Will Change Everything — Here's How",
    creator: creatorMap["diary-ceo"],
    category: "interview",
    duration: 4800,
    thumbnailGradient: getGradient("interview", 1),
    uploadDate: "2025-09-15",
    attributes: { topic: ["AI", "technology", "future"], style: "interview", tone: "serious" },
  },
  {
    id: "v-dceo-03",
    title: "Building a Billion-Dollar Brand from Nothing",
    creator: creatorMap["diary-ceo"],
    category: "interview",
    duration: 3600,
    thumbnailGradient: getGradient("interview", 2),
    uploadDate: "2025-07-10",
    attributes: { topic: ["entrepreneurship", "branding", "business"], style: "interview", tone: "energetic" },
  },

  // Johnny Harris — Commentary (3)
  {
    id: "v-jh-01",
    title: "Why Borders Are Imaginary — And Why They Matter",
    creator: creatorMap["johnny-harris"],
    category: "commentary",
    duration: 1440,
    thumbnailGradient: getGradient("commentary", 0),
    uploadDate: "2025-10-20",
    attributes: { topic: ["geopolitics", "borders", "power"], style: "essay", tone: "analytical" },
  },
  {
    id: "v-jh-02",
    title: "The Hidden Economics of Streaming Wars",
    creator: creatorMap["johnny-harris"],
    category: "commentary",
    duration: 1260,
    thumbnailGradient: getGradient("commentary", 1),
    uploadDate: "2025-08-05",
    attributes: { topic: ["economics", "media", "streaming"], style: "analysis", tone: "analytical" },
  },
  {
    id: "v-jh-03",
    title: "How Maps Lie to You Every Day",
    creator: creatorMap["johnny-harris"],
    category: "commentary",
    duration: 1080,
    thumbnailGradient: getGradient("commentary", 2),
    uploadDate: "2025-06-12",
    attributes: { topic: ["cartography", "power", "perception"], style: "essay", tone: "analytical" },
  },

  // ColdFusion — Commentary (3)
  {
    id: "v-cf-01",
    title: "The Rise and Fall of WeWork — Full Story",
    creator: creatorMap["coldfusion"],
    category: "commentary",
    duration: 1800,
    thumbnailGradient: getGradient("commentary", 0),
    uploadDate: "2025-09-28",
    attributes: { topic: ["business", "startups", "failure"], style: "documentary", tone: "analytical" },
  },
  {
    id: "v-cf-02",
    title: "How AI Chips Are Reshaping Global Power",
    creator: creatorMap["coldfusion"],
    category: "commentary",
    duration: 1560,
    thumbnailGradient: getGradient("commentary", 1),
    uploadDate: "2025-07-22",
    attributes: { topic: ["AI", "semiconductors", "geopolitics"], style: "documentary", tone: "serious" },
  },
  {
    id: "v-cf-03",
    title: "The Untold Story of the Internet's Creation",
    creator: creatorMap["coldfusion"],
    category: "commentary",
    duration: 2100,
    thumbnailGradient: getGradient("commentary", 2),
    uploadDate: "2025-05-08",
    attributes: { topic: ["internet", "history", "technology"], style: "documentary", tone: "contemplative" },
  },

  // Vox Earworm — Creative (3)
  {
    id: "v-vox-01",
    title: "Why This Beat Makes Every Song a Hit",
    creator: creatorMap["vox-earworm"],
    category: "creative",
    duration: 900,
    thumbnailGradient: getGradient("creative", 0),
    uploadDate: "2025-10-10",
    attributes: { topic: ["music", "production", "culture"], style: "documentary", tone: "playful" },
  },
  {
    id: "v-vox-02",
    title: "The Hidden Genius of Film Scores",
    creator: creatorMap["vox-earworm"],
    category: "creative",
    duration: 1080,
    thumbnailGradient: getGradient("creative", 1),
    uploadDate: "2025-08-14",
    attributes: { topic: ["film", "music", "composition"], style: "essay", tone: "contemplative" },
  },
  {
    id: "v-vox-03",
    title: "How K-Pop Conquered the World",
    creator: creatorMap["vox-earworm"],
    category: "creative",
    duration: 1200,
    thumbnailGradient: getGradient("creative", 2),
    uploadDate: "2025-06-30",
    attributes: { topic: ["K-pop", "globalization", "music industry"], style: "analysis", tone: "energetic" },
  },

  // Kirsten Dirksen — Creative (2)
  {
    id: "v-kd-01",
    title: "Living in a Converted Shipping Container Home",
    creator: creatorMap["kirsten-dirksen"],
    category: "creative",
    duration: 1500,
    thumbnailGradient: getGradient("creative", 0),
    uploadDate: "2025-09-05",
    attributes: { topic: ["architecture", "sustainability", "minimalism"], style: "documentary", tone: "contemplative" },
  },
  {
    id: "v-kd-02",
    title: "Off-Grid Family Builds Forest Paradise",
    creator: creatorMap["kirsten-dirksen"],
    category: "creative",
    duration: 1800,
    thumbnailGradient: getGradient("creative", 1),
    uploadDate: "2025-07-18",
    attributes: { topic: ["off-grid", "family", "nature"], style: "documentary", tone: "contemplative" },
  },

  // 3Blue1Brown — Educational (3)
  {
    id: "v-3b1b-01",
    title: "But What Is a Neural Network, Really?",
    creator: creatorMap["3blue1brown"],
    category: "educational",
    duration: 1140,
    thumbnailGradient: getGradient("educational", 0),
    uploadDate: "2025-10-15",
    attributes: { topic: ["neural networks", "AI", "mathematics"], style: "explainer", tone: "playful" },
  },
  {
    id: "v-3b1b-02",
    title: "The Essence of Linear Algebra",
    creator: creatorMap["3blue1brown"],
    category: "educational",
    duration: 960,
    thumbnailGradient: getGradient("educational", 1),
    uploadDate: "2025-08-22",
    attributes: { topic: ["linear algebra", "mathematics", "visualization"], style: "explainer", tone: "analytical" },
  },
  {
    id: "v-3b1b-03",
    title: "Visualizing Quaternions — An Exploration of 4D",
    creator: creatorMap["3blue1brown"],
    category: "educational",
    duration: 1320,
    thumbnailGradient: getGradient("educational", 2),
    uploadDate: "2025-06-05",
    attributes: { topic: ["quaternions", "4D", "mathematics"], style: "explainer", tone: "playful" },
  },
];

// ── Mock Recommendations ─────────────────────────────────────────────────────

export function getForYouRecommendations(
  subscriptions: string[],
  watchHistory: string[],
): Recommendation[] {
  const unwatched = videos.filter((v) => !watchHistory.includes(v.id));
  const subscribed = unwatched.filter((v) => subscriptions.includes(v.creator.id));
  const discovery = unwatched.filter((v) => !subscriptions.includes(v.creator.id));

  const subRecs: Recommendation[] = subscribed.slice(0, 7).map((video, i) => ({
    video,
    score: 0.95 - i * 0.03,
    reason: `From ${video.creator.name}, a creator you follow`,
    matchedAttributes: video.attributes.topic.slice(0, 2),
    source: "subscription" as const,
  }));

  const discoRecs: Recommendation[] = discovery.slice(0, 3).map((video, i) => ({
    video,
    score: 0.88 - i * 0.04,
    reason: `Discover ${video.creator.name} — ${video.attributes.style}`,
    matchedAttributes: video.attributes.topic.slice(0, 2),
    source: "discovery" as const,
  }));

  return [...subRecs, ...discoRecs];
}

export function getSimilarVideos(videoId: string): Recommendation[] {
  const source = videos.find((v) => v.id === videoId);
  if (!source) return [];

  return videos
    .filter((v) => v.id !== videoId)
    .map((video) => {
      const topicOverlap = video.attributes.topic.filter((t) =>
        source.attributes.topic.includes(t),
      ).length;
      const sameCreator = video.creator.id === source.creator.id;
      const score = topicOverlap * 0.3 + (sameCreator ? 0.2 : 0) + Math.random() * 0.1;
      const matched = video.attributes.topic.filter((t) => source.attributes.topic.includes(t));
      return {
        video,
        score,
        reason: sameCreator
          ? `More from ${video.creator.name}`
          : matched.length > 0
            ? `Also covers ${matched[0]}`
            : `Similar ${video.attributes.style}`,
        matchedAttributes: matched.length > 0 ? matched : [video.attributes.style],
        source: sameCreator ? ("subscription" as const) : ("discovery" as const),
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 8);
}

export function getCreatorById(id: string): Creator | undefined {
  return creators.find((c) => c.id === id);
}

export function getVideosByCreator(creatorId: string): Video[] {
  return videos.filter((v) => v.creator.id === creatorId);
}

export function getVideoById(id: string): Video | undefined {
  return videos.find((v) => v.id === id);
}

export function searchVideos(query: string): Video[] {
  const q = query.toLowerCase();
  return videos.filter(
    (v) =>
      v.title.toLowerCase().includes(q) ||
      v.creator.name.toLowerCase().includes(q) ||
      v.attributes.topic.some((t) => t.toLowerCase().includes(q)) ||
      v.attributes.style.toLowerCase().includes(q) ||
      v.category.toLowerCase().includes(q),
  );
}

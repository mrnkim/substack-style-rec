import { fetchAllVideos } from "@/lib/twelve-labs";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const creatorId = searchParams.get("creator_id");

  let videos = await fetchAllVideos();

  if (category) {
    videos = videos.filter((v) => v.category === category);
  }
  if (creatorId) {
    videos = videos.filter((v) => v.creator.id === creatorId);
  }

  return Response.json({ data: videos, total: videos.length });
}

import { fetchAllVideos, fetchCreators } from "@/lib/twelve-labs";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const [creators, videos] = await Promise.all([fetchCreators(), fetchAllVideos()]);
  const creator = creators.find((c) => c.id === id);

  if (!creator) {
    return Response.json({ error: "Creator not found" }, { status: 404 });
  }

  const creatorVideos = videos.filter((v) => v.creator.id === id);

  return Response.json({ creator, videos: creatorVideos });
}

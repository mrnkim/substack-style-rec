import { fetchVideoById } from "@/lib/twelve-labs";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const video = await fetchVideoById(id);

  if (!video) {
    return Response.json({ error: "Video not found" }, { status: 404 });
  }

  return Response.json(video);
}

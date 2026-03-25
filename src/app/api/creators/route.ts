import { fetchCreators } from "@/lib/twelve-labs";

export async function GET() {
  const creators = await fetchCreators();
  return Response.json({ data: creators });
}

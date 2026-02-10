import { proxyGet } from "@/app/api/proxy";

export async function GET(request: Request, { params }: { params: { slug: string } }) {
  return proxyGet(request, `/public/masters/${params.slug}`, {
    cacheControl: "public, s-maxage=300, stale-while-revalidate=600",
    cacheMode: "force-cache",
    revalidate: 300
  });
}

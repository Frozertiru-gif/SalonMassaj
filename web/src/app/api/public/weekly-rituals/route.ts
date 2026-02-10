import { proxyGet } from "@/app/api/proxy";

export async function GET(request: Request) {
  return proxyGet(request, "/public/weekly-rituals", {
    cacheControl: "public, s-maxage=300, stale-while-revalidate=600",
    cacheMode: "force-cache",
    revalidate: 300
  });
}

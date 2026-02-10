import { proxyGet } from "@/app/api/proxy";

export async function GET(request: Request) {
  return proxyGet(request, "/public/settings/contacts", {
    cacheControl: "public, s-maxage=600, stale-while-revalidate=1200",
    cacheMode: "force-cache",
    revalidate: 600
  });
}

import { proxyGet } from "@/app/api/proxy";

export async function GET(request: Request) {
  return proxyGet(request, "/public/reviews");
}

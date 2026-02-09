import { proxyPost } from "@/app/api/proxy";

export async function POST(request: Request) {
  return proxyPost(request, "/public/bookings");
}

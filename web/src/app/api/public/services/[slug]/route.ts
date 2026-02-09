import { proxyGet } from "@/app/api/proxy";

type RouteContext = {
  params: {
    slug: string;
  };
};

export async function GET(request: Request, context: RouteContext) {
  const { slug } = context.params;
  return proxyGet(request, `/public/services/${encodeURIComponent(slug)}`);
}

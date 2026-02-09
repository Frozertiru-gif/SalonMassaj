import { proxyGet } from "@/app/api/proxy";

interface RouteParams {
  params: {
    slug: string;
  };
}

export async function GET(request: Request, { params }: RouteParams) {
  return proxyGet(request, `/public/services/${params.slug}`);
}

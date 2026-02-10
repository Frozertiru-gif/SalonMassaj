import { NextResponse } from "next/server";

const API_INTERNAL_BASE_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

type ProxyOptions = {
  cacheControl?: string;
  cacheMode?: RequestCache;
  revalidate?: number;
};

function buildTargetUrl(request: Request, path: string) {
  const targetUrl = new URL(path, API_INTERNAL_BASE_URL);
  const requestUrl = new URL(request.url);
  targetUrl.search = requestUrl.search;
  return targetUrl.toString();
}

async function proxyRequest(request: Request, path: string, init?: RequestInit, options?: ProxyOptions) {
  const targetUrl = buildTargetUrl(request, path);

  try {
    const response = await fetch(targetUrl, {
      ...init,
      cache: options?.cacheMode ?? "no-store",
      next: options?.revalidate ? { revalidate: options.revalidate } : undefined
    });

    const body = await response.text();
    const headers = new Headers();
    const contentType = response.headers.get("content-type");

    if (contentType) {
      headers.set("content-type", contentType);
    }

    headers.set("cache-control", options?.cacheControl ?? "no-store");

    return new NextResponse(body, {
      status: response.status,
      headers
    });
  } catch {
    return NextResponse.json(
      { error: "Upstream unavailable" },
      { status: 502, headers: { "cache-control": "no-store" } }
    );
  }
}

export async function proxyGet(request: Request, path: string, options?: ProxyOptions) {
  return proxyRequest(request, path, undefined, options);
}

export async function proxyPost(request: Request, path: string) {
  const body = await request.text();
  return proxyRequest(
    request,
    path,
    {
      method: "POST",
      body,
      headers: {
        "Content-Type": request.headers.get("content-type") ?? "application/json"
      }
    },
    { cacheMode: "no-store", cacheControl: "no-store" }
  );
}

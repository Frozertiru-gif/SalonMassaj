import { NextResponse } from "next/server";

const API_INTERNAL_BASE_URL =
  process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

function buildTargetUrl(request: Request, path: string) {
  const targetUrl = new URL(path, API_INTERNAL_BASE_URL);
  const requestUrl = new URL(request.url);
  targetUrl.search = requestUrl.search;
  return targetUrl.toString();
}

async function proxyRequest(request: Request, path: string, init?: RequestInit) {
  const targetUrl = buildTargetUrl(request, path);
  try {
    const response = await fetch(targetUrl, {
      ...init,
      cache: "no-store"
    });
    const body = await response.text();
    const headers = new Headers();
    const contentType = response.headers.get("content-type");
    if (contentType) {
      headers.set("content-type", contentType);
    }
    headers.set("cache-control", "no-store");
    return new NextResponse(body, {
      status: response.status,
      headers
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Upstream unavailable" },
      { status: 502, headers: { "cache-control": "no-store" } }
    );
  }
}

export async function proxyGet(request: Request, path: string) {
  return proxyRequest(request, path);
}

export async function proxyPost(request: Request, path: string) {
  const body = await request.text();
  return proxyRequest(request, path, {
    method: "POST",
    body,
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json"
    }
  });
}

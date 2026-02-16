import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ADMIN_TOKEN_COOKIE } from "@/lib/auth";

const API_INTERNAL_BASE_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

export async function GET(request: Request) {
  const token = cookies().get(ADMIN_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const response = await fetch(`${API_INTERNAL_BASE_URL}/admin/schedule${new URL(request.url).search}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });

  const proxied = new NextResponse(await response.text(), {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store"
    }
  });

  if (response.status === 401 || response.status === 403) {
    proxied.cookies.set(ADMIN_TOKEN_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true, sameSite: "lax" });
  }

  return proxied;
}

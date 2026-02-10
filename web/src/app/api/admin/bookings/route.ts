import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ADMIN_TOKEN_COOKIE } from "@/lib/auth";

const API_INTERNAL_BASE_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const token = cookies().get(ADMIN_TOKEN_COOKIE)?.value;
  if (!token) {
    const response = NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    response.cookies.set(ADMIN_TOKEN_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true, sameSite: "lax" });
    return response;
  }

  const response = await fetch(`${API_INTERNAL_BASE_URL}/admin/bookings`, {
    method: "POST",
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
      Authorization: `Bearer ${token}`
    },
    body: await request.text(),
    cache: "no-store"
  });

  const body = await response.text();
  const proxiedResponse = new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store"
    }
  });

  if (response.status === 401 || response.status === 403) {
    proxiedResponse.cookies.set(ADMIN_TOKEN_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true, sameSite: "lax" });
  }

  return proxiedResponse;
}

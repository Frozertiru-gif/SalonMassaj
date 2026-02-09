import { cookies } from "next/headers";

const API_BASE_URL = "/api";
const API_SERVER_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

export async function publicFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = cookies().get("admin_token")?.value;
  if (!token) {
    throw new Error("Missing admin token");
  }
  const response = await fetch(`${API_SERVER_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `API error: ${response.status}`);
  }
  return (await response.json()) as T;
}

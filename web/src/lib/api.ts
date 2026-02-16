import { cookies } from "next/headers";
import { ADMIN_TOKEN_COOKIE, isAuthDetail, redirectToAdminLogin } from "@/lib/auth";

type PublicFetchInit = RequestInit & {
  revalidate?: number;
};

type AdminFetchInit = RequestInit & {
  currentPath?: string;
};

const API_SERVER_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

export class ServiceUnavailableError extends Error {
  constructor() {
    super("Сервис временно недоступен");
    this.name = "ServiceUnavailableError";
  }
}

function isServiceUnavailableStatus(status: number): boolean {
  return status === 502 || status === 503 || status === 504;
}

function getAuthErrorDetail(data: unknown): string | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const detail = "detail" in data ? (data as { detail?: unknown }).detail : undefined;
  return typeof detail === "string" ? detail : null;
}

function getErrorMessage(status: number, data: unknown, fallbackText: string | null): string {
  if (data && typeof data === "object") {
    const detail = "detail" in data ? (data as { detail?: unknown }).detail : undefined;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }
          const msg = "msg" in item ? (item as { msg?: unknown }).msg : undefined;
          return typeof msg === "string" ? msg : null;
        })
        .filter((msg): msg is string => Boolean(msg));
      if (messages.length) {
        return messages.join("; ");
      }
    }

    const message = "message" in data ? (data as { message?: unknown }).message : undefined;
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  if (fallbackText && fallbackText.trim()) {
    return fallbackText.trim();
  }

  return `HTTP ${status}`;
}

export async function publicFetch<T>(path: string, init?: PublicFetchInit): Promise<T> {
  const { revalidate = 300, ...requestInit } = init ?? {};
  const response = await fetch(`${API_SERVER_URL}${path}`, {
    ...requestInit,
    ...(requestInit.cache ? {} : { next: { revalidate, ...(requestInit.next ?? {}) } })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function adminFetchResponse(path: string, init?: AdminFetchInit): Promise<Response> {
  const { currentPath, ...requestInit } = init ?? {};
  const token = cookies().get(ADMIN_TOKEN_COOKIE)?.value;

  if (!token) {
    redirectToAdminLogin(currentPath);
  }

  let response: Response;
  try {
    response = await fetch(`${API_SERVER_URL}${path}`, {
      ...requestInit,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(requestInit.headers ?? {})
      },
      cache: "no-store"
    });
  } catch {
    throw new ServiceUnavailableError();
  }

  if (response.status === 401 || response.status === 403) {
    redirectToAdminLogin(currentPath);
  }

  if (!response.ok) {
    if (isServiceUnavailableStatus(response.status)) {
      throw new ServiceUnavailableError();
    }

    if (response.status === 401 || response.status === 403) {
      const data = await response.clone().json().catch(() => null);
      const detail = getAuthErrorDetail(data);
      if (isAuthDetail(detail)) {
        redirectToAdminLogin(currentPath);
      }
    }
  }

  return response;
}

export async function adminFetch<T>(path: string, init?: AdminFetchInit): Promise<T> {
  const response = await adminFetchResponse(path, init);

  if (!response.ok) {
    const cloned = response.clone();
    const data = await cloned.json().catch(() => null);
    const textBody = data ? null : await response.text().catch(() => null);
    throw new Error(getErrorMessage(response.status, data, textBody));
  }

  return (await response.json()) as T;
}

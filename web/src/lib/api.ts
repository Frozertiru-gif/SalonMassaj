import { cookies } from "next/headers";
import { redirect } from "next/navigation";

type PublicFetchInit = RequestInit & {
  revalidate?: number;
};

type AdminFetchInit = RequestInit & {
  currentPath?: string;
};

const API_SERVER_URL = process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";
const ADMIN_LOGIN_PATH = "/admin/login";

export class ServiceUnavailableError extends Error {
  constructor() {
    super("Сервис временно недоступен");
    this.name = "ServiceUnavailableError";
  }
}

function isServiceUnavailableStatus(status: number): boolean {
  return status === 502 || status === 503 || status === 504;
}

function shouldSkipLoginRedirect(currentPath?: string): boolean {
  return currentPath === ADMIN_LOGIN_PATH;
}

function handleAdminAuthFailure(currentPath?: string): never {
  if (typeof window === "undefined") {
    cookies().delete("admin_token");
    if (!shouldSkipLoginRedirect(currentPath)) {
      redirect(ADMIN_LOGIN_PATH);
    }
  }

  if (!shouldSkipLoginRedirect(currentPath ?? window.location.pathname)) {
    window.location.replace(ADMIN_LOGIN_PATH);
  }

  throw new Error("Требуется повторный вход в админ-панель");
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

export async function adminFetch<T>(path: string, init?: AdminFetchInit): Promise<T> {
  const { currentPath, ...requestInit } = init ?? {};
  const token = cookies().get("admin_token")?.value;

  if (!token) {
    handleAdminAuthFailure(currentPath);
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
    handleAdminAuthFailure(currentPath);
  }

  if (!response.ok) {
    if (isServiceUnavailableStatus(response.status)) {
      throw new ServiceUnavailableError();
    }

    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `API error: ${response.status}`);
  }

  return (await response.json()) as T;
}

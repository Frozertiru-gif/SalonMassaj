import { buildAdminLoginUrl, isAuthDetail } from "@/lib/auth/shared";

function getAuthErrorDetail(data: unknown): string | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const detail = "detail" in data ? (data as { detail?: unknown }).detail : undefined;
  return typeof detail === "string" ? detail : null;
}

export function clientAdminRedirect(nextPath?: string) {
  window.location.replace(buildAdminLoginUrl(nextPath ?? `${window.location.pathname}${window.location.search}`));
}

export async function clientAdminFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, init);
  if (response.status === 401 || response.status === 403) {
    clientAdminRedirect();
    return response;
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = getAuthErrorDetail(data);
    if (isAuthDetail(detail)) {
      clientAdminRedirect();
    }
  }

  return response;
}

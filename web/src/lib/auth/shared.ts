export const ADMIN_LOGIN_PATH = "/admin/login";
export const ADMIN_TOKEN_COOKIE = "admin_token";

const AUTH_ERROR_DETAILS = [
  "not authenticated",
  "unauthorized",
  "invalid token",
  "token expired",
  "expired token",
  "inactive admin"
];

export function isJwtLikeToken(token: string): boolean {
  const parts = token.split(".");
  return parts.length === 3 && parts.every((part) => part.length > 0);
}

export function normalizeAdminNextPath(value?: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/admin";
  }
  if (!value.startsWith("/admin") || value.startsWith(ADMIN_LOGIN_PATH)) {
    return "/admin";
  }
  return value;
}

export function buildAdminLoginUrl(nextPath?: string): string {
  const loginUrl = new URL(ADMIN_LOGIN_PATH, "http://localhost");
  const normalizedNext = normalizeAdminNextPath(nextPath);
  if (normalizedNext !== "/admin") {
    loginUrl.searchParams.set("next", normalizedNext);
  }
  return `${loginUrl.pathname}${loginUrl.search}`;
}

export function isAuthDetail(detail?: string | null): boolean {
  if (!detail) {
    return false;
  }

  const normalized = detail.toLowerCase();
  return AUTH_ERROR_DETAILS.some((item) => normalized.includes(item));
}

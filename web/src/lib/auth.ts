import { redirect } from "next/navigation";
import { buildAdminLoginUrl } from "@/lib/auth/shared";

export { ADMIN_LOGIN_PATH, ADMIN_TOKEN_COOKIE, buildAdminLoginUrl, isAuthDetail, normalizeAdminNextPath } from "@/lib/auth/shared";

export function redirectToAdminLogin(nextPath?: string): never {
  const loginUrl = buildAdminLoginUrl(nextPath);

  if (typeof window !== "undefined") {
    window.location.assign(loginUrl);
    throw new Error("Client redirect to admin login");
  }

  redirect(loginUrl);
}

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ADMIN_TOKEN_COOKIE, buildAdminLoginUrl } from "@/lib/auth/shared";

export { ADMIN_LOGIN_PATH, ADMIN_TOKEN_COOKIE, buildAdminLoginUrl, isAuthDetail, normalizeAdminNextPath } from "@/lib/auth/shared";

export function clearAdminAuthCookie() {
  cookies().set(ADMIN_TOKEN_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0
  });
}

export function redirectToAdminLogin(nextPath?: string): never {
  clearAdminAuthCookie();
  redirect(buildAdminLoginUrl(nextPath));
}

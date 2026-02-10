import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import {
  ADMIN_LOGIN_PATH,
  ADMIN_TOKEN_COOKIE,
  buildAdminLoginUrl,
  isJwtLikeToken
} from "@/lib/auth/shared";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (pathname === ADMIN_LOGIN_PATH) {
    return NextResponse.next();
  }

  const token = request.cookies.get(ADMIN_TOKEN_COOKIE)?.value;
  if (!token || !isJwtLikeToken(token)) {
    const url = new URL(buildAdminLoginUrl(`${pathname}${search}`), request.url);
    const response = NextResponse.redirect(url);
    response.cookies.set(ADMIN_TOKEN_COOKIE, "", {
      path: "/",
      maxAge: 0,
      httpOnly: true,
      sameSite: "lax"
    });
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"]
};

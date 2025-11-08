import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import { jwtVerify } from "jose";

import { JWT_SECRET } from "@/lib/config";

import { routing } from "./i18n/routing";

const secret = new TextEncoder().encode(JWT_SECRET);

const handleI18nRouting = createMiddleware(routing);

export const config = {
  matcher: ["/((?!api|trpc|_next|_vercel|.*\\..*).*)"],
};

export async function proxy(req: NextRequest) {
  const response = handleI18nRouting(req);

  // TO-DO: broken
  const locale = req.nextUrl.pathname.split("/")[1];

  if (req.nextUrl.pathname.startsWith(`/${locale}/admin`)) {
    const token = req.cookies.get("token")?.value;
    if (!token) {
      return NextResponse.redirect(new URL("/login", req.url));
    }

    try {
      const { payload } = await jwtVerify(token, secret);
      if (payload.role !== "admin") {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    } catch {
      return NextResponse.redirect(new URL("/login", req.url));
    }
  }

  return response;
}

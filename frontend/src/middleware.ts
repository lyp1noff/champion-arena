import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const secret = new TextEncoder().encode(process.env.JWT_SECRET!);
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function middleware(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const refreshToken = req.cookies.get("refresh_token")?.value;
  const path = req.nextUrl.pathname;

  async function tryRefresh() {
    const refreshRes = await fetch(`${backendUrl}/auth/refresh`, {
      method: "POST",
      headers: {
        cookie: req.headers.get("cookie") || "",
        "Content-Type": "application/json",
      },
    });

    if (refreshRes.ok) {
      const setCookie = refreshRes.headers.get("set-cookie");
      if (setCookie) {
        const res = NextResponse.next();
        res.headers.set("set-cookie", setCookie);
        return res;
      }
      return NextResponse.next();
    }
    return null;
  }

  if (!token && refreshToken) {
    const refreshed = await tryRefresh();
    if (refreshed) return refreshed;
    if (path.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    return NextResponse.next();
  }

  if (token) {
    try {
      const { payload } = await jwtVerify(token, secret);
      if (path.startsWith("/admin") && payload.role !== "admin") {
        return NextResponse.redirect(new URL("/login", req.url));
      }
      return NextResponse.next();
    } catch {
      if (refreshToken) {
        const refreshed = await tryRefresh();
        if (refreshed) return refreshed;
      }
      if (path.startsWith("/admin")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
      return NextResponse.next();
    }
  }

  if (path.startsWith("/admin")) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};

import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const secret = new TextEncoder().encode(process.env.JWT_SECRET!);

export async function middleware(req: NextRequest) {
  const token = req.cookies.get("token")?.value;
  const path = req.nextUrl.pathname;

  if (!token) {
    if (path.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    return NextResponse.next();
  }

  try {
    const { payload } = await jwtVerify(token, secret);

    if (path.startsWith("/admin") && payload.role !== "admin") {
      return NextResponse.redirect(new URL("/login", req.url));
    }

    return NextResponse.next();
  } catch {
    if (path.startsWith("/admin")) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    return NextResponse.next();
  }
}

export const config = {
  matcher: ["/admin/:path*"],
};

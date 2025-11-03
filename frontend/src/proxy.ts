import { type NextRequest, NextResponse } from "next/server";

import { jwtVerify } from "jose";

import { JWT_SECRET } from "@/lib/config";

const secret = new TextEncoder().encode(JWT_SECRET!);

export const config = {
  matcher: "/admin/:path*",
};

export async function proxy(req: NextRequest) {
  const token = req.cookies.get("token")?.value;

  if (!token) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  try {
    const { payload } = await jwtVerify(token, secret);

    if (payload.role !== "admin") {
      return NextResponse.redirect(new URL("/login", req.url));
    }

    return NextResponse.next();
  } catch {
    return NextResponse.redirect(new URL("/login", req.url));
  }
}

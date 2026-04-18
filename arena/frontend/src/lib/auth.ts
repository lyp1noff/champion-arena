import { cookies } from "next/headers";

import { jwtVerify } from "jose";

import { JWT_SECRET } from "@/lib/config";

interface AuthPayload {
  sub: string;
  exp: number;
  role?: string;
}

const secret = new TextEncoder().encode(JWT_SECRET!);

export async function verifyTokenFromCookie(): Promise<AuthPayload | null> {
  const cookiesInstance = await cookies();
  const token = cookiesInstance.get("token")?.value;

  if (!token) return null;

  try {
    const { payload } = await jwtVerify<AuthPayload>(token, secret);

    return payload;
  } catch {
    return null;
  }
}

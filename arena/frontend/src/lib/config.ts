export const CDN_URL = process.env.NEXT_PUBLIC_CDN_URL || "https://cdn.example.com";
export const BACKEND_URL =
  typeof window === "undefined" ? process.env.BACKEND_INTERNAL_URL || "/api" : "/api";
export const JWT_SECRET = process.env.JWT_SECRET || "default-secret";
export const ANALYTICS_URL = process.env.NEXT_PUBLIC_ANALYTICS_URL;
export const ANALYTICS_ID = process.env.NEXT_PUBLIC_ANALYTICS_ID;

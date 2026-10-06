export const CDN_URL = process.env.NEXT_PUBLIC_CDN_URL || "https://cdn.example.com";
const PUBLIC_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
export const BACKEND_URL =
  typeof window === "undefined" ? process.env.BACKEND_INTERNAL_URL || PUBLIC_BACKEND_URL : PUBLIC_BACKEND_URL;
export const JWT_SECRET = process.env.JWT_SECRET || "default-secret";
export const ANALYTICS_URL = process.env.NEXT_PUBLIC_ANALYTICS_URL;
export const ANALYTICS_ID = process.env.NEXT_PUBLIC_ANALYTICS_ID;

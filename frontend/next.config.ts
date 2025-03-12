import type { NextConfig } from "next";

const CDN_URL = process.env.NEXT_PUBLIC_CDN_URL || "https://cdn.example.com";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: new URL(CDN_URL).hostname,
        port: "",
        pathname: "/**",
        search: "",
      },
    ],
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: false,
  },
  output: "standalone",
};

export default nextConfig;

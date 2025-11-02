import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

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
  output: "standalone",
};

const withNextIntl = createNextIntlPlugin();
export default withNextIntl(nextConfig);

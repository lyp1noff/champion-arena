import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

import { CDN_URL } from "@/lib/config";

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

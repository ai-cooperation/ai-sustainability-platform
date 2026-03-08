import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/ai-sustainability-platform",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

import path from "node:path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname, "../.."),
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;

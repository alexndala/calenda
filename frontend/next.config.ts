import type { NextConfig } from "next";

let backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
if (!/^https?:\/\//.test(backendUrl)) {
  backendUrl = `http://${backendUrl}`;
}

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // NextAuth routes must NOT be rewritten — they're handled by Next.js itself.
      // Everything under /api/auth/** stays local.
      {
        source: "/api/sessions/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/sessions/:path*`,
      },
      {
        source: "/api/classify",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/classify`,
      },
      {
        source: "/api/mcq/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/mcq/:path*`,
      },
      {
        source: "/api/exports/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/exports/:path*`,
      },
      {
        source: "/api/famous/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/famous/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/static/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
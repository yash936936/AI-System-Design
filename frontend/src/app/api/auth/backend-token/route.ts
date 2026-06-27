/**
 * POST /api/auth/backend-token
 *
 * Called client-side to exchange a NextAuth session for a short-lived
 * FastAPI bearer token.  The response is stored in memory (Zustand) for the
 * lifetime of the browser tab.
 *
 * Flow:
 *   1. Verify the caller has a valid NextAuth session (getServerSession).
 *   2. Build a minimal JWT signed with INTERNAL_AUTH_SECRET.
 *   3. Return { token, expiresAt } — the frontend attaches it as
 *      `Authorization: Bearer <token>` on every FastAPI call.
 *
 * We use the `jose` library (already a transitive dep of next-auth) to sign
 * the JWT so we don't need an extra package.
 */
import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { SignJWT } from "jose"
import { authOptions } from "@/lib/auth"

const SECRET = new TextEncoder().encode(
  process.env.INTERNAL_AUTH_SECRET ?? "dev-secret-change-me"
)

export async function POST() {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const user = session.user as any
  const userId: string = user.userId ?? user.email ?? "anonymous"

  // 1-hour token — short enough to rotate, long enough not to annoy.
  const expiresAt = Math.floor(Date.now() / 1000) + 60 * 60

  const token = await new SignJWT({
    sub: userId,
    email: user.email ?? "",
    name: user.name ?? "",
    provider: user.provider ?? "unknown",
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(expiresAt)
    .sign(SECRET)

  return NextResponse.json({ token, expiresAt, userId })
}
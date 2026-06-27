"use client"

/**
 * useAuth — thin wrapper around NextAuth's `useSession` that additionally:
 *   1. Fetches a short-lived FastAPI bearer token via /api/auth/backend-token.
 *   2. Caches it in module-level state so the token survives React re-renders
 *      without a round-trip on every render.
 *   3. Refreshes the token 5 minutes before it expires.
 *
 * Usage:
 *   const { session, backendToken, userId, signOut } = useAuth()
 *   // attach backendToken to FastAPI calls:
 *   fetch("/api/sessions", { headers: { Authorization: `Bearer ${backendToken}` } })
 */

import { useSession, signOut as nextAuthSignOut } from "next-auth/react"
import { useEffect, useRef, useState } from "react"

interface BackendTokenCache {
  token: string
  expiresAt: number   // Unix epoch seconds
  userId: string
}

// Module-level cache — survives component unmount/remount.
let _cache: BackendTokenCache | null = null

async function fetchBackendToken(): Promise<BackendTokenCache> {
  const res = await fetch("/api/auth/backend-token", { method: "POST" })
  if (!res.ok) throw new Error("Failed to fetch backend token")
  return res.json()
}

function isExpiringSoon(expiresAt: number): boolean {
  // Refresh 5 minutes before expiry.
  return Date.now() / 1000 > expiresAt - 300
}

export function useAuth() {
  const { data: session, status } = useSession()
  const [backendToken, setBackendToken] = useState<string | null>(_cache?.token ?? null)
  const [userId, setUserId] = useState<string | null>(_cache?.userId ?? null)
  const fetchingRef = useRef(false)

  useEffect(() => {
    if (status !== "authenticated") return
    if (_cache && !isExpiringSoon(_cache.expiresAt)) {
      setBackendToken(_cache.token)
      setUserId(_cache.userId)
      return
    }
    if (fetchingRef.current) return

    fetchingRef.current = true
    fetchBackendToken()
      .then((data) => {
        _cache = data
        setBackendToken(data.token)
        setUserId(data.userId)
      })
      .catch((err) => {
        console.error("[useAuth] backend-token fetch failed:", err)
      })
      .finally(() => {
        fetchingRef.current = false
      })
  }, [status])

  /**
   * Attach the backend bearer token to a standard Headers object.
   * Use this when building fetch() calls to FastAPI.
   */
  function authHeaders(): Record<string, string> {
    if (!backendToken) return {}
    return { Authorization: `Bearer ${backendToken}` }
  }

  function signOut() {
    _cache = null
    nextAuthSignOut({ callbackUrl: "/signin" })
  }

  return {
    session,
    status,
    backendToken,
    userId,
    authHeaders,
    signOut,
    isAuthenticated: status === "authenticated" && !!backendToken,
  }
}
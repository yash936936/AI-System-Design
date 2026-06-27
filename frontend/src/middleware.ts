/**
 * Route protection middleware.
 *
 * Public routes: /signin, /api/auth/**, /static/**
 * Everything else requires a valid NextAuth session.
 */
import { withAuth } from "next-auth/middleware"
import { NextResponse } from "next/server"

export default withAuth(
  function middleware(req) {
    // Token exists — allow the request through.
    return NextResponse.next()
  },
  {
    callbacks: {
      /**
       * Return true to allow; return false to redirect to the signIn page.
       * withAuth already populates `req.nextauth.token` for us.
       */
      authorized({ token }) {
        return !!token
      },
    },
    pages: {
      signIn: "/signin",
    },
  }
)

export const config = {
  /**
   * Match every route EXCEPT:
   *   - /signin                (the login page itself)
   *   - /api/auth/**           (NextAuth callbacks/csrf/session endpoints)
   *   - /_next/**              (Next.js internals)
   *   - /static/**             (FastAPI-proxied static files)
   *   - /favicon.ico, images…
   */
  matcher: [
    "/((?!signin|api/auth|_next/static|_next/image|static|favicon\\.ico).*)",
  ],
}
/**
 * NextAuth configuration — shared by:
 *   - src/app/api/auth/[...nextauth]/route.ts  (route handler)
 *   - Server components / server actions via `getServerSession(authOptions)`
 */
import { type NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import GitHubProvider from "next-auth/providers/github"

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID ?? "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
    }),
  ],

  pages: {
    signIn: "/signin",
  },

  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  callbacks: {
    /**
     * Enrich the JWT with the provider's user id so we can pass it to the
     * FastAPI backend as the stable `user_id` value.
     */
    async jwt({ token, account, profile }) {
      if (account) {
        token.provider = account.provider
        // Use the sub from the provider as a stable cross-session user id.
        // e.g.  "google_109876543210"  or  "github_1234567"
        token.userId = `${account.provider}_${token.sub}`
      }
      return token
    },

    /**
     * Expose userId and provider to the client via useSession().
     */
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).userId = token.userId
        ;(session.user as any).provider = token.provider
      }
      return session
    },
  },

  secret: process.env.NEXTAUTH_SECRET,
}
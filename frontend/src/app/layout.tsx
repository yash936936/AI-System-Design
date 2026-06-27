import type { Metadata } from "next"
import './globals.css';
import AuthProvider from "@/components/auth/AuthProvider"

export const metadata: Metadata = {
  title: "SysDesign AI",
  description: "System design assistant - HLD & LLD powered by Gemini",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface-black text-ink-white font-lambo antialiased h-screen overflow-hidden">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
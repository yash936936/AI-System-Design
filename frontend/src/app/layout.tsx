import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "SysDesign AI",
  description: "System design assistant — HLD & LLD powered by Gemini",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg-base text-text-primary antialiased h-screen overflow-hidden">
        {children}
      </body>
    </html>
  )
}

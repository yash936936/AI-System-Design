"use client"

import { useState, useEffect } from "react"
import { LogOut, ChevronDown, User, Sun, Moon, RefreshCw } from "lucide-react"
import { useAuth } from "@/hooks/useAuth"

export default function UserMenu() {
  const { session, signOut } = useAuth()
  const [open, setOpen] = useState(false)
  const [theme, setTheme] = useState<"dark" | "light">("dark")

  useEffect(() => {
    const stored = localStorage.getItem("sysdesign-theme") as "dark" | "light" | null
    if (stored) setTheme(stored)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle("light-theme", theme === "light")
    localStorage.setItem("sysdesign-theme", theme)
  }, [theme])

  if (!session?.user) return null

  const { name, email, image } = session.user

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-sm hover:bg-surface-charcoal transition-colors"
      >
        {image ? (
          <img
            src={image}
            alt={name ?? "avatar"}
            className="w-7 h-7 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-7 h-7 rounded-full bg-gold flex items-center justify-center flex-shrink-0">
            <User size={14} className="text-surface-black" />
          </div>
        )}

        <div className="flex-1 text-left overflow-hidden">
          <div className="text-ink-white text-xs font-lambo tracking-wider truncate uppercase">
            {name ?? "User"}
          </div>
          <div className="text-ink-ash text-[10px] truncate">{email}</div>
        </div>

        <ChevronDown
          size={12}
          className={`text-ink-steel transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          />
          {/* Dropdown */}
          <div className="absolute bottom-full mb-1 left-0 right-0 z-20 bg-surface-charcoal border border-ink-shadow rounded-sm shadow-lg overflow-hidden">
            {/* Theme toggle */}
            <button
              onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}
              className="flex items-center gap-2 w-full px-3 py-2.5 text-xs font-lambo tracking-wider uppercase text-ink-ash hover:text-gold hover:bg-surface-iron transition-colors"
            >
              {theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </button>

            {/* Switch account */}
            <button
              onClick={() => { setOpen(false); signOut() }}
              className="flex items-center gap-2 w-full px-3 py-2.5 text-xs font-lambo tracking-wider uppercase text-ink-ash hover:text-gold hover:bg-surface-iron transition-colors"
            >
              <RefreshCw size={13} />
              Switch Account
            </button>

            <div className="border-t border-ink-shadow" />

            {/* Sign out */}
            <button
              onClick={() => { setOpen(false); signOut() }}
              className="flex items-center gap-2 w-full px-3 py-2.5 text-xs font-lambo tracking-wider uppercase text-ink-ash hover:text-gold hover:bg-surface-iron transition-colors"
            >
              <LogOut size={13} />
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  )
}
// frontend/src/components/layout/Sidebar.tsx
"use client"
import { useState, useEffect } from "react"
import { PlusIcon, MessageSquareIcon, XIcon, Loader2Icon, PanelLeftCloseIcon, PanelLeftOpenIcon, SunIcon, MoonIcon } from "lucide-react"
import { useStore, hydrateSessionHistory } from "@/store/useStore"
import { getSession } from "@/lib/api"
import { LogoLockup } from "@/components/brand/Logo"
import UserMenu from "@/components/auth/UserMenu"
import { useTheme } from "@/components/ThemeContext"

export default function Sidebar() {
  const { sessionHistory, session, resetSession, loadSession, removeFromHistory, addMessage } = useStore()
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const { theme, toggleTheme } = useTheme()

  useEffect(() => {
    hydrateSessionHistory()
  }, [])

  const handleSelectHistory = async (id: string, title: string) => {
    if (loadingId) return
    setLoadingId(id)
    try {
      const data = await getSession(id)
      loadSession(data, title)
    } catch (err) {
      console.error("Failed to load session:", err)
      addMessage("assistant", "error", "Couldn't reload that session — it may have been removed from the server.")
    } finally {
      setLoadingId(null)
    }
  }

  const handleRemove = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    removeFromHistory(id)
  }

  if (collapsed) {
    return (
      <aside className="w-12 flex flex-col h-full bg-surface-black border-r border-[#202020] shrink-0 items-center py-4 gap-3">
        <button onClick={() => setCollapsed(false)} title="Expand sidebar" className="theme-toggle">
          <PanelLeftOpenIcon size={18} />
        </button>
        <button onClick={resetSession} title="New design" className="theme-toggle">
          <PlusIcon size={18} />
        </button>
        <div className="mt-auto">
          <button
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="theme-toggle"
          >
            {theme === "dark" ? <SunIcon size={16} /> : <MoonIcon size={16} />}
          </button>
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-sidebar flex flex-col h-full bg-surface-black border-r border-[#202020] shrink-0">

      <div className="flex items-center justify-between px-5 pt-6 pb-4">
        <LogoLockup />
        <button onClick={() => setCollapsed(true)} title="Collapse sidebar" className="theme-toggle -mr-1">
          <PanelLeftCloseIcon size={16} />
        </button>
      </div>

      <div className="px-4 pb-4">
        <button onClick={resetSession} className="btn-accent w-full px-4 py-3">
          <PlusIcon size={15} strokeWidth={2.5} />
          New Design
        </button>
      </div>

      <div className="px-5 py-2">
        <span className="label-caps">Recent</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 space-y-0.5">
        {sessionHistory.length === 0 && (
          <p className="text-btnsm text-ink-steel px-2 py-6 text-center uppercase tracking-wide">
            Your designs will appear here
          </p>
        )}
        {sessionHistory.map((item) => {
          const isActive = item.id === session.id
          const isLoading = loadingId === item.id
          return (
            <button
              key={item.id}
              onClick={() => handleSelectHistory(item.id, item.title)}
              disabled={isLoading}
              className={`
                group w-full flex items-start gap-2.5 px-3 py-3 rounded-none text-left
                text-body transition-colors duration-150
                ${isActive ? "bg-surface-charcoal text-ink-white" : "text-ink-ash hover:bg-surface-charcoal hover:text-ink-white"}
                ${isLoading ? "opacity-60 cursor-wait" : ""}
              `}
            >
              {isLoading ? (
                <Loader2Icon size={14} className="mt-0.5 shrink-0 text-gold animate-spin" />
              ) : (
                <MessageSquareIcon size={14} className={`mt-0.5 shrink-0 ${isActive ? "text-gold" : "text-ink-steel"}`} />
              )}
              <div className="min-w-0 flex-1">
                <p className="truncate">{item.title}</p>
                <p className="text-micro uppercase tracking-wide text-ink-steel mt-0.5">
                  {new Date(item.date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  {item.designType ? ` · ${item.designType}` : ""}
                </p>
              </div>
              <span
                role="button"
                aria-label="Remove from history"
                onClick={(e) => handleRemove(e, item.id)}
                className="opacity-0 group-hover:opacity-100 shrink-0 p-1 -mr-1 mt-0.5 text-ink-steel hover:text-ink-white transition-opacity"
              >
                <XIcon size={13} />
              </span>
            </button>
          )
        })}
      </nav>

      <div className="px-3 pt-3 border-t border-[#202020] flex items-center justify-between">
        <UserMenu />
        <button
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="theme-toggle shrink-0"
        >
          {theme === "dark" ? <SunIcon size={15} /> : <MoonIcon size={15} />}
        </button>
      </div>
    </aside>
  )
}
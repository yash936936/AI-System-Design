"use client"
import { PlusIcon, MessageSquareIcon, BrainCircuitIcon } from "lucide-react"
import { useStore } from "@/store/useStore"

export default function Sidebar() {
  const { sessionHistory, resetSession } = useStore()

  return (
    <aside className="w-sidebar flex flex-col h-full bg-bg-sidebar border-r border-border shrink-0">

      {/* Logo */}
      <div className="px-4 pt-5 pb-3 flex items-center gap-2">
        <BrainCircuitIcon size={20} className="text-accent-primary" />
        <span className="font-semibold text-base text-text-primary tracking-tight">SysDesign AI</span>
      </div>

      {/* New Chat button */}
      <div className="px-3 pb-3">
        <button
          onClick={resetSession}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
                     text-sm text-text-primary bg-bg-hover hover:bg-bg-input
                     transition-colors duration-150 border border-border"
        >
          <PlusIcon size={15} />
          New Design
        </button>
      </div>

      <div className="px-4 py-1">
        <span className="text-xs text-text-muted uppercase tracking-widest font-medium">Recent</span>
      </div>

      {/* History list */}
      <nav className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {sessionHistory.length === 0 && (
          <p className="text-xs text-text-muted px-3 py-4 text-center">
            Your designs will appear here
          </p>
        )}
        {sessionHistory.map((item) => (
          <button
            key={item.id}
            className="w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left
                       text-sm text-text-secondary hover:bg-bg-hover hover:text-text-primary
                       transition-colors duration-150"
          >
            <MessageSquareIcon size={14} className="mt-0.5 shrink-0 text-text-muted" />
            <div className="min-w-0">
              <p className="truncate">{item.title}</p>
              <p className="text-xs text-text-muted">{item.date}</p>
            </div>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <p className="text-xs text-text-muted">
          Powered by Gemini Flash · Free tier
        </p>
      </div>
    </aside>
  )
}

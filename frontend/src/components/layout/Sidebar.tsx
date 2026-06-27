"use client"
import { PlusIcon, MessageSquareIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import { LogoLockup } from "@/components/brand/Logo"

export default function Sidebar() {
  const { sessionHistory, resetSession } = useStore()

  return (
    <aside className="w-sidebar flex flex-col h-full bg-surface-black border-r border-[#202020] shrink-0">

      {/* Logo — brand mark + uppercase wordmark */}
      <div className="px-5 pt-6 pb-4">
        <LogoLockup />
      </div>

      {/* New Design — Gold Accent CTA */}
      <div className="px-4 pb-4">
        <button
          onClick={resetSession}
          className="btn-accent w-full px-4 py-3"
        >
          <PlusIcon size={15} strokeWidth={2.5} />
          New Design
        </button>
      </div>

      <div className="px-5 py-2">
        <span className="label-caps">Recent</span>
      </div>

      {/* History list */}
      <nav className="flex-1 overflow-y-auto px-3 space-y-0.5">
        {sessionHistory.length === 0 && (
          <p className="text-btnsm text-ink-steel px-2 py-6 text-center uppercase tracking-wide">
            Your designs will appear here
          </p>
        )}
        {sessionHistory.map((item) => (
          <button
            key={item.id}
            className="w-full flex items-start gap-2.5 px-3 py-3 rounded-none text-left
                       text-body text-ink-ash hover:bg-surface-charcoal hover:text-ink-white
                       transition-colors duration-150"
          >
            <MessageSquareIcon size={14} className="mt-0.5 shrink-0 text-ink-steel" />
            <div className="min-w-0">
              <p className="truncate">{item.title}</p>
              <p className="text-micro uppercase tracking-wide text-ink-steel mt-0.5">{item.date}</p>
            </div>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[#202020]">
        <p className="text-micro uppercase tracking-wide text-ink-ash">
          Powered by Gemini Flash · Free Tier
        </p>
      </div>
    </aside>
  )
}
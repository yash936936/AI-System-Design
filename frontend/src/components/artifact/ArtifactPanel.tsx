"use client"
import { clsx } from "clsx"
import { XIcon, LayoutIcon, ActivityIcon, DatabaseIcon, CodeIcon, LayersIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import type { ArtifactTab } from "@/types"

const TABS: { id: ArtifactTab; label: string; icon: React.ReactNode }[] = [
  { id: "diagram",    label: "Diagram",     icon: <LayoutIcon size={13} /> },
  { id: "capacity",   label: "Capacity",    icon: <ActivityIcon size={13} /> },
  { id: "data_model", label: "Data Model",  icon: <DatabaseIcon size={13} /> },
  { id: "api",        label: "API",         icon: <CodeIcon size={13} /> },
  { id: "stack",      label: "Stack",       icon: <LayersIcon size={13} /> },
  { id: "sources",    label: "Sources",     icon: <ActivityIcon size={13} /> },
]

function EmptyTab({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 space-y-2">
      <p className="text-body text-ink-white uppercase tracking-wide">{label}</p>
      <p className="text-micro uppercase tracking-wide text-ink-steel">Available after generation completes (Stage 4)</p>
    </div>
  )
}

export default function ArtifactPanel() {
  const { artifact, setArtifactTab, setArtifactVisible } = useStore()

  if (!artifact.isVisible) return null

  return (
    <aside className="w-artifact flex flex-col h-full bg-surface-black border-l border-[#202020] shrink-0">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#202020]">
        <span className="text-body font-medium text-ink-white uppercase tracking-wide">Design Output</span>
        <button
          onClick={() => setArtifactVisible(false)}
          className="p-1 text-ink-steel hover:text-ink-white transition-colors"
        >
          <XIcon size={15} />
        </button>
      </div>

      {/* Tab bar — sharp underline tabs, gold active state */}
      <div className="flex gap-1 px-3 border-b border-[#202020] overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setArtifactTab(tab.id)}
            className={clsx("artifact-tab flex items-center gap-1.5 whitespace-nowrap", {
              active: artifact.activeTab === tab.id,
            })}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {artifact.activeTab === "diagram" && (
          artifact.diagram
            ? <DiagramView data={artifact.diagram} />
            : <EmptyTab label="Architecture Diagram" />
        )}
        {artifact.activeTab === "capacity" && (
          artifact.capacity
            ? <JsonView data={artifact.capacity} />
            : <EmptyTab label="Capacity Estimation" />
        )}
        {artifact.activeTab === "data_model" && (
          artifact.data_model
            ? <JsonView data={artifact.data_model} />
            : <EmptyTab label="Data Model" />
        )}
        {artifact.activeTab === "api" && (
          artifact.api_design
            ? <JsonView data={artifact.api_design} />
            : <EmptyTab label="API Design" />
        )}
        {artifact.activeTab === "stack" && (
          artifact.stack
            ? <JsonView data={artifact.stack} />
            : <EmptyTab label="Tech Stack" />
        )}
        {artifact.activeTab === "sources" && (
          artifact.sources
            ? <SourcesView chunks={artifact.sources} />
            : <EmptyTab label="RAG Sources" />
        )}
      </div>
    </aside>
  )
}

// ── Sub-views ─────────────────────────────────────────────────────────────────

function DiagramView({ data }: { data: { components: unknown[] } }) {
  return (
    <div className="p-4 space-y-2.5">
      <p className="text-micro uppercase tracking-wide text-ink-steel">{data.components.length} components</p>
      {(data.components as Array<{ id: string; name: string; type: string; description: string }>).map((c) => (
        <div key={c.id} className="card border border-white/10 px-3.5 py-3 space-y-1">
          <div className="flex items-center gap-2.5">
            <span className={clsx("w-2 h-2", componentColor(c.type))} />
            <span className="text-body font-medium text-ink-white">{c.name}</span>
            <span className="text-micro uppercase tracking-wide text-ink-steel ml-auto">{c.type}</span>
          </div>
          <p className="text-btnsm text-ink-ash pl-4">{c.description}</p>
        </div>
      ))}
      <p className="text-micro uppercase tracking-wide text-ink-steel pt-2">
        Interactive React Flow diagram activates in Stage 4
      </p>
    </div>
  )
}

function JsonView({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="p-4 text-btnsm text-ink-ash font-mono whitespace-pre-wrap leading-relaxed">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function SourcesView({ chunks }: { chunks: Array<{ id: string; source: string; section: string; text: string; score: number }> }) {
  return (
    <div className="p-4 space-y-3">
      {chunks.map((chunk) => (
        <div key={chunk.id} className="card border border-white/10 p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-btnsm font-medium text-ink-white">{chunk.source}</span>
            <span className="badge">{Math.round(chunk.score * 100)}% match</span>
          </div>
          <p className="text-micro uppercase tracking-wide text-ink-steel">{chunk.section}</p>
          <div className="w-full h-1 bg-white/10">
            <div
              className="h-1 bg-gold"
              style={{ width: `${chunk.score * 100}%` }}
            />
          </div>
          <p className="text-btnsm text-ink-ash line-clamp-3">{chunk.text}</p>
        </div>
      ))}
    </div>
  )
}

// Component-type dots kept inside the documented palette (gold/cyan/link-blue
// plus the achromatic ink ramp) instead of an arbitrary rainbow, per the
// "no additional accent colors beyond gold" rule in the design system.
function componentColor(type: string): string {
  const map: Record<string, string> = {
    frontend:    "bg-ink-white",
    backend:     "bg-cyan-pulse",
    database:    "bg-gold",
    queue:       "bg-ink-steel",
    cache:       "bg-ink-ash",
    cdn:         "bg-ink-graphite",
    auth:        "bg-gold-text",
    storage:     "bg-ink-smoke",
    third_party: "bg-ink-slate",
    ai:          "bg-link-blue",
  }
  return map[type] ?? "bg-ink-steel"
}
"use client"
import { clsx } from "clsx"
import { XIcon, LayoutIcon, ActivityIcon, DatabaseIcon, CodeIcon, StacksIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import type { ArtifactTab } from "@/types"

const TABS: { id: ArtifactTab; label: string; icon: React.ReactNode }[] = [
  { id: "diagram",    label: "Diagram",     icon: <LayoutIcon size={13} /> },
  { id: "capacity",   label: "Capacity",    icon: <ActivityIcon size={13} /> },
  { id: "data_model", label: "Data Model",  icon: <DatabaseIcon size={13} /> },
  { id: "api",        label: "API",         icon: <CodeIcon size={13} /> },
  { id: "stack",      label: "Stack",       icon: <LayoutIcon size={13} /> },
  { id: "sources",    label: "Sources",     icon: <ActivityIcon size={13} /> },
]

function EmptyTab({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 space-y-2">
      <p className="text-sm text-text-secondary font-medium">{label}</p>
      <p className="text-xs text-text-muted">Available after generation completes (Stage 4)</p>
    </div>
  )
}

export default function ArtifactPanel() {
  const { artifact, setArtifactTab, setArtifactVisible } = useStore()

  if (!artifact.isVisible) return null

  return (
    <aside className="w-artifact flex flex-col h-full bg-bg-artifact border-l border-border shrink-0">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">Design Output</span>
        <button
          onClick={() => setArtifactVisible(false)}
          className="p-1 rounded text-text-muted hover:text-text-primary transition-colors"
        >
          <XIcon size={14} />
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 px-3 py-2 border-b border-border overflow-x-auto">
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
    <div className="p-4 space-y-2">
      <p className="text-xs text-text-muted">{data.components.length} components</p>
      {(data.components as Array<{ id: string; name: string; type: string; description: string }>).map((c) => (
        <div key={c.id} className="bg-bg-input border border-border rounded-lg px-3 py-2 space-y-0.5">
          <div className="flex items-center gap-2">
            <span className={clsx("w-2 h-2 rounded-full", componentColor(c.type))} />
            <span className="text-sm font-medium text-text-primary">{c.name}</span>
            <span className="text-xs text-text-muted ml-auto">{c.type}</span>
          </div>
          <p className="text-xs text-text-secondary pl-4">{c.description}</p>
        </div>
      ))}
      <p className="text-xs text-text-muted pt-2">
        Interactive React Flow diagram activates in Stage 4
      </p>
    </div>
  )
}

function JsonView({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="p-4 text-xs text-text-secondary font-mono whitespace-pre-wrap leading-relaxed">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function SourcesView({ chunks }: { chunks: Array<{ id: string; source: string; section: string; text: string; score: number }> }) {
  return (
    <div className="p-4 space-y-3">
      {chunks.map((chunk) => (
        <div key={chunk.id} className="bg-bg-input border border-border rounded-lg p-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-primary">{chunk.source}</span>
            <span className="text-xs text-accent-primary">{Math.round(chunk.score * 100)}% match</span>
          </div>
          <p className="text-xs text-text-secondary">{chunk.section}</p>
          <div className="w-full h-1 bg-bg-hover rounded-full">
            <div
              className="h-1 rounded-full bg-accent-primary"
              style={{ width: `${chunk.score * 100}%` }}
            />
          </div>
          <p className="text-xs text-text-muted line-clamp-3">{chunk.text}</p>
        </div>
      ))}
    </div>
  )
}

function componentColor(type: string): string {
  const map: Record<string, string> = {
    frontend:    "bg-blue-400",
    backend:     "bg-green-400",
    database:    "bg-orange-400",
    queue:       "bg-purple-400",
    cache:       "bg-yellow-400",
    cdn:         "bg-gray-400",
    auth:        "bg-red-400",
    storage:     "bg-teal-400",
    third_party: "bg-pink-400",
    ai:          "bg-indigo-400",
  }
  return map[type] ?? "bg-gray-400"
}

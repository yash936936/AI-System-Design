"use client"
import { useStore } from "@/store/useStore"
import type { ArtifactTab } from "@/types"

const TABS: { id: ArtifactTab; label: string; icon: string }[] = [
  { id: "diagram", label: "Diagram", icon: "◈" },
  { id: "capacity", label: "Capacity", icon: "⚡" },
  { id: "data_model", label: "Data Model", icon: "⬡" },
  { id: "api", label: "API", icon: "⟷" },
  { id: "stack", label: "Stack", icon: "⎔" },
]

export default function ArtifactPanel() {
  const { artifact, setArtifactTab } = useStore()

  if (!artifact.isVisible) return null

  return (
    <div className="w-[480px] h-full bg-ink-black border-l border-ink-graphite flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-ink-graphite">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setArtifactTab(tab.id)}
            className={`flex-1 py-3 px-2 text-xs font-mono uppercase tracking-wider transition-colors ${
              artifact.activeTab === tab.id
                ? "text-gold border-b-2 border-gold bg-ink-charcoal"
                : "text-ink-steel hover:text-ink-ash"
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {artifact.activeTab === "diagram" && artifact.diagram && (
          <DiagramView data={artifact.diagram} />
        )}
        {artifact.activeTab === "capacity" && artifact.capacity && (
          <CapacityView data={artifact.capacity} />
        )}
        {artifact.activeTab === "data_model" && artifact.data_model && (
          <DataModelView data={artifact.data_model} />
        )}
        {artifact.activeTab === "api" && artifact.api && (
          <ApiView data={artifact.api} />
        )}
        {artifact.activeTab === "stack" && artifact.stack && (
          <StackView data={artifact.stack} />
        )}
        {!artifact[artifact.activeTab] && (
          <div className="text-ink-steel text-sm">
            Waiting for generation…
          </div>
        )}
      </div>
    </div>
  )
}

// ── Diagram View ──────────────────────────────────────────────────────────────

function componentColor(type: string): string {
  const map: Record<string, string> = {
    frontend: "bg-ink-white",
    backend: "bg-cyan-pulse",
    database: "bg-gold",
    queue: "bg-ink-steel",
    cache: "bg-ink-ash",
    cdn: "bg-ink-graphite",
    auth: "bg-gold-text",
    storage: "bg-ink-smoke",
    third_party: "bg-ink-slate",
    ai: "bg-link-blue",
  }
  return map[type] ?? "bg-ink-steel"
}

function DiagramView({ data }: { data: { components: any[] } }) {
  return (
    <div className="space-y-4">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">
        Architecture Components
      </h2>
      <p className="text-ink-steel text-xs">
        {data.components.length} components
      </p>
      <div className="space-y-3">
        {data.components.map((c) => (
          <div key={c.id} className="bg-ink-charcoal border border-ink-graphite p-3">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${componentColor(c.type)}`} />
              <span className="text-ink-white text-sm font-mono">{c.name}</span>
              <span className="text-ink-steel text-xs ml-auto">{c.type}</span>
            </div>
            <p className="text-ink-ash text-xs">{c.description}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {c.connections?.map((conn: string) => (
                <span key={conn} className="text-[10px] bg-ink-graphite text-ink-steel px-1.5 py-0.5">
                  → {conn}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Capacity View ─────────────────────────────────────────────────────────────

function CapacityView({ data }: { data: any }) {
  const metrics = [
    { label: "DAU", value: data.dau?.toLocaleString(), unit: "" },
    { label: "Peak Read QPS", value: data.peak_read_qps?.toLocaleString(), unit: "req/s" },
    { label: "Peak Write QPS", value: data.peak_write_qps?.toLocaleString(), unit: "req/s" },
    { label: "Daily Storage", value: data.daily_storage_gb, unit: "GB" },
    { label: "5-Year Storage", value: data.five_year_storage_tb, unit: "TB" },
    { label: "Bandwidth", value: data.bandwidth_gbps, unit: "Gbps" },
    { label: "Cache Dataset", value: data.cache_dataset_gb, unit: "GB" },
  ]

  return (
    <div className="space-y-4">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">
        Capacity Estimation
      </h2>
      <div className="space-y-2">
        {metrics.map((m) => (
          <div key={m.label} className="flex justify-between items-baseline bg-ink-charcoal border border-ink-graphite p-3">
            <span className="text-ink-steel text-xs">{m.label}</span>
            <span className="text-ink-white font-mono text-sm">
              {m.value} <span className="text-ink-steel text-xs">{m.unit}</span>
            </span>
          </div>
        ))}
      </div>
      {data.formulas && (
        <div className="mt-4">
          <h3 className="text-ink-ash text-xs font-mono uppercase mb-2">Formulas</h3>
          <div className="space-y-1">
            {Object.entries(data.formulas).map(([key, formula]) => (
              <div key={key} className="bg-ink-charcoal border border-ink-graphite p-2">
                <span className="text-gold-text text-xs font-mono">{key}:</span>
                <p className="text-ink-ash text-xs mt-1">{formula as string}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Data Model View ───────────────────────────────────────────────────────────

function DataModelView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">
        Data Model
      </h2>
      <div className="bg-ink-charcoal border border-ink-graphite p-3">
        <span className="text-ink-steel text-xs">Decision:</span>
        <span className="text-gold font-mono text-sm ml-2">{data.decision}</span>
      </div>
      <p className="text-ink-ash text-xs">{data.rationale}</p>
      <div className="space-y-3">
        {data.entities?.map((entity: any) => (
          <div key={entity.name} className="bg-ink-charcoal border border-ink-graphite p-3">
            <h3 className="text-cyan-pulse font-mono text-sm mb-2">{entity.name}</h3>
            <div className="space-y-1">
              {entity.columns?.map((col: any) => (
                <div key={col.name} className="flex items-center gap-2 text-xs">
                  <span className="text-ink-white font-mono">{col.name}</span>
                  <span className="text-ink-steel">{col.type}</span>
                  {col.primary && <span className="text-gold text-[10px]">PK</span>}
                  {col.indexed && <span className="text-cyan-pulse text-[10px]">IDX</span>}
                </div>
              ))}
            </div>
            {entity.sharding_key && (
              <p className="text-ink-steel text-xs mt-2">
                Sharding: <span className="text-gold-text">{entity.sharding_key}</span>
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── API View ──────────────────────────────────────────────────────────────────

function ApiView({ data }: { data: any }) {
  const methodColors: Record<string, string> = {
    GET: "text-cyan-pulse",
    POST: "text-gold",
    PUT: "text-ink-white",
    DELETE: "text-red-400",
    PATCH: "text-ink-ash",
  }

  return (
    <div className="space-y-4">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">
        API Design
      </h2>
      <div className="flex gap-4">
        <div className="bg-ink-charcoal border border-ink-graphite p-2">
          <span className="text-ink-steel text-xs">Style:</span>
          <span className="text-ink-white font-mono text-sm ml-2">{data.style}</span>
        </div>
        <div className="bg-ink-charcoal border border-ink-graphite p-2">
          <span className="text-ink-steel text-xs">Auth:</span>
          <span className="text-ink-white font-mono text-sm ml-2">{data.auth}</span>
        </div>
      </div>
      <div className="space-y-2">
        {data.endpoints?.map((ep: any, i: number) => (
          <div key={i} className="bg-ink-charcoal border border-ink-graphite p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className={`font-mono text-xs font-bold ${methodColors[ep.method] || "text-ink-white"}`}>
                {ep.method}
              </span>
              <span className="text-ink-white font-mono text-sm">{ep.path}</span>
            </div>
            <p className="text-ink-ash text-xs">{ep.description}</p>
            {ep.rate_limit && (
              <p className="text-ink-steel text-xs mt-1">Rate: {ep.rate_limit}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Stack View ────────────────────────────────────────────────────────────────

function StackView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">
        Tech Stack
      </h2>
      <div className="space-y-3">
        {data.layers?.map((layer: any) => (
          <div key={layer.layer} className="bg-ink-charcoal border border-ink-graphite p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-ink-steel text-xs uppercase">{layer.layer}</span>
              <span className="text-gold font-mono text-sm">{layer.primary}</span>
            </div>
            <p className="text-ink-ash text-xs mb-2">{layer.rationale}</p>
            {layer.alternatives?.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {layer.alternatives.map((alt: string) => (
                  <span key={alt} className="text-[10px] bg-ink-graphite text-ink-steel px-1.5 py-0.5">
                    {alt}
                  </span>
                ))}
              </div>
            )}
            {layer.trade_off && (
              <p className="text-ink-steel text-xs italic">Trade-off: {layer.trade_off}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
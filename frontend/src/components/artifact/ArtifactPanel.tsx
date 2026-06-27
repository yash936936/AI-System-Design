"use client"
import {
  WorkflowIcon,
  ZapIcon,
  DatabaseIcon,
  ArrowLeftRightIcon,
  LayersIcon,
  LockIcon,
  XIcon,
  PanelRightOpenIcon,
  type LucideIcon,
} from "lucide-react"
import { useStore } from "@/store/useStore"
import DiagramFlow from "./DiagramFlow"
import type { ArtifactTab, ArchitectureData, CapacityData, DataModelData, ApiDesignData, StackData } from "@/types"


// ── Tab definitions ───────────────────────────────────────────────────────────
const TABS: { id: ArtifactTab; label: string; icon: LucideIcon }[] = [
  { id: "diagram",     label: "Diagram",    icon: WorkflowIcon },
  { id: "capacity",    label: "Capacity",   icon: ZapIcon },
  { id: "data_model",  label: "Data Model", icon: DatabaseIcon },
  { id: "api",         label: "API",        icon: ArrowLeftRightIcon },
  { id: "stack",       label: "Stack",      icon: LayersIcon },
]

// Map from ArtifactTab id to the artifact state key holding that section's data
const TAB_DATA_KEY: Record<ArtifactTab, keyof ReturnType<typeof useStore.getState>["artifact"]> = {
  diagram:    "diagram",
  capacity:   "capacity",
  data_model: "data_model",
  api:        "api",
  stack:      "stack",
}

export default function ArtifactPanel() {
  const { artifact, setArtifactTab, setArtifactVisible } = useStore()

  // Collapsed state — the panel was never opened yet, or the user closed it.
  // Previously this returned `null`, which removed every button along with
  // it, so once hidden there was no way to bring the panel back. Render a
  // slim reopen strip instead so the user always has a way back in.
  if (!artifact.isVisible) {
    return (
      <div className="h-full w-12 bg-ink-black border-l border-ink-graphite flex flex-col items-center pt-4 shrink-0">
        <button
          onClick={() => setArtifactVisible(true)}
          title="Open design artifacts"
          className="p-2 text-ink-steel hover:text-gold hover:bg-ink-charcoal transition-colors rounded"
        >
          <PanelRightOpenIcon className="w-5 h-5" />
        </button>
      </div>
    )
  }

  const activeData = artifact[TAB_DATA_KEY[artifact.activeTab]]
  const activeLoading = artifact.loading?.[artifact.activeTab]
  const activeError = artifact.errors?.[artifact.activeTab]

  return (
    <div className="w-[480px] h-full bg-ink-black border-l border-ink-graphite flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink-graphite shrink-0">
        <span className="text-ink-ash text-xs font-mono uppercase tracking-wider">Design Artifacts</span>
        <button
          onClick={() => setArtifactVisible(false)}
          title="Close artifact panel"
          className="p-1 text-ink-steel hover:text-ink-white hover:bg-ink-charcoal transition-colors rounded"
        >
          <XIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-ink-graphite shrink-0">
        {TABS.map((tab) => {
          const hasData = Boolean(artifact[TAB_DATA_KEY[tab.id]])
          const isLoading = Boolean(artifact.loading?.[tab.id])
          const isActive = artifact.activeTab === tab.id
          const Icon = tab.icon

          return (
            <button
              key={tab.id}
              onClick={() => setArtifactTab(tab.id)}
              className={`
                flex-1 py-3 px-2 text-xs font-mono uppercase tracking-wider transition-colors relative
                flex items-center justify-center gap-1.5
                ${isActive
                  ? "text-gold border-b-2 border-gold bg-ink-charcoal"
                  : "text-ink-steel hover:text-ink-ash"}
              `}
            >
              {/* Loading dot indicator */}
              {isLoading && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-gold rounded-full animate-pulse" />
              )}
              {/* Done dot indicator */}
              {!isLoading && hasData && !isActive && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-green-500 rounded-full" />
              )}
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Loading state */}
        {activeLoading && !activeData && (
          <LoadingState label={TABS.find((t) => t.id === artifact.activeTab)?.label ?? "section"} />
        )}

        {/* Error state */}
        {activeError && !activeData && (
          <ErrorState message={activeError} />
        )}

        {/* Section content */}
        {!activeLoading && !activeError && !activeData && (
          <WaitingState />
        )}

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
      </div>
    </div>
  )
}

// ── State placeholders ────────────────────────────────────────────────────────

function WaitingState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center py-16">
      <div className="w-10 h-10 border border-ink-graphite mb-4 flex items-center justify-center">
        <span className="text-ink-graphite font-mono text-lg">·</span>
      </div>
      <p className="text-ink-steel text-sm">
        Waiting for generation…
      </p>
      <p className="text-ink-graphite text-xs mt-1">
        This section will appear as the pipeline runs.
      </p>
    </div>
  )
}

function LoadingState({ label }: { label: string }) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center py-16">
      <div className="flex gap-1.5 mb-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 bg-gold rounded-full animate-pulse"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
      <p className="text-ink-ash text-sm">Generating {label}…</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-950/30 border border-red-800/50 p-4 rounded">
      <p className="text-red-400 text-xs font-mono uppercase tracking-wide mb-1">Generation error</p>
      <p className="text-red-300 text-sm">{message}</p>
    </div>
  )
}

// ── Helper: type badge ────────────────────────────────────────────────────────
function Badge({ label, color = "text-ink-steel bg-ink-graphite" }: { label: string; color?: string }) {
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 ${color}`}>
      {label}
    </span>
  )
}

// ── Diagram View ──────────────────────────────────────────────────────────────

function componentColor(type: string): string {
  const map: Record<string, string> = {
    frontend:    "bg-blue-400",
    client:      "bg-blue-400",
    backend:     "bg-cyan-400",
    gateway:     "bg-teal-400",
    database:    "bg-yellow-400",
    queue:       "bg-purple-400",
    cache:       "bg-green-400",
    cdn:         "bg-gray-400",
    auth:        "bg-orange-400",
    storage:     "bg-pink-400",
    third_party: "bg-indigo-400",
    external:    "bg-indigo-400",
    ai:          "bg-red-400",
  }
  return map[type] ?? "bg-ink-steel"
}

function DiagramView({ data }: { data: ArchitectureData & Record<string, any> }) {
  const components = data.components ?? []
  const dataFlows = data.data_flows ?? []
  const deploymentZones = data.deployment_zones ?? []
  const decisions = data.key_design_decisions ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h2 className="text-gold font-mono text-sm uppercase tracking-wider">Architecture Components</h2>
        <span className="text-ink-steel text-xs">{components.length} components</span>
      </div>

      {/* Interactive React Flow diagram */}
      <DiagramFlow data={data} />

      {/* Component cards */}
      <div className="space-y-3">
        {components.map((c: any) => (
          <div key={c.id} className="bg-ink-charcoal border border-ink-graphite p-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full shrink-0 ${componentColor(c.type)}`} />
              <span className="text-ink-white text-sm font-mono font-medium">{c.name}</span>
              <Badge label={c.type} color="text-ink-steel bg-ink-graphite" />
              {c.technology && (
                <Badge label={c.technology} color="text-gold-text bg-ink-graphite" />
              )}
            </div>
            <p className="text-ink-ash text-xs leading-relaxed">{c.description}</p>
            {c.responsibilities?.length > 0 && (
              <ul className="space-y-0.5">
                {c.responsibilities.map((r: string, i: number) => (
                  <li key={i} className="text-ink-steel text-xs flex gap-1">
                    <span className="text-gold shrink-0">·</span> {r}
                  </li>
                ))}
              </ul>
            )}
            {c.connections?.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1 border-t border-ink-graphite">
                {c.connections.map((conn: string) => (
                  <span key={conn} className="text-[10px] bg-ink-graphite text-ink-steel px-1.5 py-0.5 font-mono">
                    → {conn}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Data flows */}
      {dataFlows.length > 0 && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Data Flows</h3>
          <div className="space-y-1.5">
            {dataFlows.map((flow: any, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-cyan-400 font-mono">{flow.from}</span>
                <span className="text-ink-steel">→</span>
                <span className="text-cyan-400 font-mono">{flow.to}</span>
                {flow.label && <span className="text-ink-steel ml-auto">{flow.label}</span>}
                {flow.protocol && <Badge label={flow.protocol} color="text-gold-text bg-ink-graphite" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deployment zones */}
      {deploymentZones.length > 0 && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Deployment Zones</h3>
          <div className="space-y-1.5">
            {deploymentZones.map((zone: any, i: number) => (
              <div key={i} className="bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-gold text-xs font-mono">{zone.zone}</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {zone.components?.map((c: string) => (
                    <Badge key={c} label={c} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key design decisions */}
      {decisions.length > 0 && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Key Decisions</h3>
          <ul className="space-y-2">
            {decisions.map((d: string, i: number) => (
              <li key={i} className="text-ink-ash text-xs flex gap-2">
                <span className="text-gold shrink-0">{i + 1}.</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Capacity View ─────────────────────────────────────────────────────────────

function CapacityView({ data }: { data: CapacityData & Record<string, any> }) {
  const metrics = [
    { label: "Daily Active Users", value: data.dau?.toLocaleString(), unit: "" },
    { label: "Peak Read QPS",      value: data.peak_read_qps?.toLocaleString(), unit: "req/s" },
    { label: "Peak Write QPS",     value: data.peak_write_qps?.toLocaleString(), unit: "req/s" },
    { label: "Daily Storage",      value: data.daily_storage_gb, unit: "GB" },
    { label: "5-Year Storage",     value: data.five_year_storage_tb, unit: "TB" },
    { label: "Bandwidth",          value: data.bandwidth_gbps, unit: "Gbps" },
    { label: "Cache Dataset",      value: data.cache_dataset_gb, unit: "GB" },
    ...(data.replication_factor != null
      ? [{ label: "Replication Factor", value: data.replication_factor, unit: "×" }]
      : []),
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">Capacity Estimation</h2>

      {/* Metrics grid */}
      <div className="space-y-2">
        {metrics.map((m) => (
          m.value != null && (
            <div
              key={m.label}
              className="flex justify-between items-baseline bg-ink-charcoal border border-ink-graphite px-3 py-2.5"
            >
              <span className="text-ink-steel text-xs">{m.label}</span>
              <span className="text-ink-white font-mono text-sm">
                {m.value}{" "}
                {m.unit && <span className="text-ink-steel text-xs">{m.unit}</span>}
              </span>
            </div>
          )
        ))}
      </div>

      {/* Formulas */}
      {data.formulas && Object.keys(data.formulas).length > 0 && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Derivation Formulas</h3>
          <div className="space-y-2">
            {Object.entries(data.formulas).map(([key, formula]) => (
              <div key={key} className="bg-ink-charcoal border border-ink-graphite p-3">
                <span className="text-gold-text text-xs font-mono">{key}:</span>
                <p className="text-ink-ash text-xs mt-1 leading-relaxed">{formula as string}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scaling notes */}
      {data.scaling_notes && (
        <div className="bg-ink-charcoal border border-ink-graphite p-3">
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-1">Scaling Notes</h3>
          <p className="text-ink-ash text-xs leading-relaxed">{data.scaling_notes}</p>
        </div>
      )}

      {/* Assumptions */}
      {data.assumptions && data.assumptions.length > 0 && (
  <div>
    <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Assumptions</h3>
    <ul className="space-y-1">
      {data.assumptions.map((a: string, i: number) => (
        <li key={i} className="text-ink-ash text-xs flex gap-2">
          <span className="text-gold shrink-0">·</span> {a}
        </li>
      ))}
    </ul>
  </div>
)}
    </div>
  )
}

// ── Data Model View ───────────────────────────────────────────────────────────

function DataModelView({ data }: { data: DataModelData & Record<string, any> }) {
  const entities = data.entities ?? []
  const secondaryStores: string[] = data.secondary_stores ?? []

  return (
    <div className="space-y-6">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">Data Model</h2>

      {/* Decision banner */}
      <div className="bg-ink-charcoal border border-ink-graphite p-3 flex items-center gap-3">
        <span className="text-ink-steel text-xs">Decision:</span>
        <span className="text-gold font-mono text-sm font-medium">{data.decision}</span>
        {data.primary_store && (
          <>
            <span className="text-ink-graphite">|</span>
            <span className="text-ink-ash text-xs">{data.primary_store}</span>
          </>
        )}
      </div>

      {/* Rationale */}
      {data.rationale && (
        <p className="text-ink-ash text-xs leading-relaxed">{data.rationale}</p>
      )}

      {/* Secondary stores */}
      {secondaryStores.length > 0 && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Secondary Stores</h3>
          <div className="flex flex-wrap gap-1.5">
            {secondaryStores.map((s: string) => (
              <Badge key={s} label={s} color="text-ink-ash bg-ink-charcoal border border-ink-graphite" />
            ))}
          </div>
        </div>
      )}

      {/* Entity cards */}
      <div className="space-y-4">
        {entities.map((entity: any) => (
          <div key={entity.name} className="bg-ink-charcoal border border-ink-graphite p-3 space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-cyan-400 font-mono text-sm">{entity.name}</h3>
              {entity.store && <Badge label={entity.store} color="text-gold-text bg-ink-graphite" />}
            </div>

            {/* Columns table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-ink-steel border-b border-ink-graphite">
                    <th className="text-left pb-1 pr-2 font-mono">column</th>
                    <th className="text-left pb-1 pr-2 font-mono">type</th>
                    <th className="text-left pb-1 font-mono">flags</th>
                  </tr>
                </thead>
                <tbody>
                  {entity.columns?.map((col: any) => (
                    <tr key={col.name} className="border-b border-ink-graphite/40">
                      <td className="py-1 pr-2 font-mono text-ink-white">{col.name}</td>
                      <td className="py-1 pr-2 text-ink-steel">{col.type}</td>
                      <td className="py-1 flex gap-1 flex-wrap">
                        {col.primary && <Badge label="PK" color="text-gold bg-ink-graphite" />}
                        {col.indexed && <Badge label="IDX" color="text-cyan-400 bg-ink-graphite" />}
                        {col.nullable === false && <Badge label="NOT NULL" color="text-ink-steel bg-ink-graphite" />}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {entity.sharding_key && (
              <p className="text-ink-steel text-xs">
                Sharding key:{" "}
                <span className="text-gold-text font-mono">{entity.sharding_key}</span>
              </p>
            )}
            {entity.partition_strategy && (
              <p className="text-ink-steel text-xs leading-relaxed">{entity.partition_strategy}</p>
            )}
            {entity.access_patterns?.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1 border-t border-ink-graphite">
                {entity.access_patterns.map((p: string, i: number) => (
                  <Badge key={i} label={p} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Caching strategy */}
      {data.caching_strategy && (
        <div className="bg-ink-charcoal border border-ink-graphite p-3">
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-1">Caching Strategy</h3>
          <p className="text-ink-ash text-xs leading-relaxed">{data.caching_strategy}</p>
        </div>
      )}

      {/* Notes */}
      {data.notes && (
        <p className="text-ink-steel text-xs italic">{data.notes}</p>
      )}
    </div>
  )
}

// ── API View ──────────────────────────────────────────────────────────────────

function ApiView({ data }: { data: ApiDesignData & Record<string, any> }) {
  const methodColors: Record<string, string> = {
    GET:    "text-cyan-400",
    POST:   "text-gold",
    PUT:    "text-blue-400",
    DELETE: "text-red-400",
    PATCH:  "text-orange-400",
  }

  const endpoints = data.endpoints ?? []

  return (
    <div className="space-y-6">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">API Design</h2>

      {/* Meta row */}
      <div className="flex flex-wrap gap-2">
        {data.style && (
          <div className="bg-ink-charcoal border border-ink-graphite px-3 py-2">
            <span className="text-ink-steel text-xs">Style:</span>
            <span className="text-ink-white font-mono text-sm ml-2">{data.style}</span>
          </div>
        )}
        {data.auth && (
          <div className="bg-ink-charcoal border border-ink-graphite px-3 py-2">
            <span className="text-ink-steel text-xs">Auth:</span>
            <span className="text-ink-white font-mono text-sm ml-2">{data.auth}</span>
          </div>
        )}
        {data.versioning && (
          <div className="bg-ink-charcoal border border-ink-graphite px-3 py-2">
            <span className="text-ink-steel text-xs">Versioning:</span>
            <span className="text-ink-white font-mono text-sm ml-2">{data.versioning}</span>
          </div>
        )}
        {(data.base_url || data.version) && (
          <div className="bg-ink-charcoal border border-ink-graphite px-3 py-2">
            <span className="text-ink-steel text-xs">Base URL:</span>
            <span className="text-ink-white font-mono text-sm ml-2">
              {data.base_url ?? ""}{data.version ? `/${data.version}` : ""}
            </span>
          </div>
        )}
      </div>

      {/* Rate limiting */}
      {data.rate_limiting && (
        <div className="bg-ink-charcoal border border-ink-graphite p-3">
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-1">Rate Limiting</h3>
          <p className="text-ink-ash text-xs">{data.rate_limiting}</p>
        </div>
      )}

      {/* Endpoints */}
      <div className="space-y-3">
        {endpoints.map((ep: any, i: number) => (
          <div key={i} className="bg-ink-charcoal border border-ink-graphite p-3 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`font-mono text-xs font-bold ${methodColors[ep.method] ?? "text-ink-white"}`}>
                {ep.method}
              </span>
              <span className="text-ink-white font-mono text-sm">{ep.path}</span>
              {ep.auth_required != null && (
                <span
                  className={`inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 ${
                    ep.auth_required ? "text-orange-400 bg-ink-graphite" : "text-green-400 bg-ink-graphite"
                  }`}
                >
                  {ep.auth_required && <LockIcon className="w-2.5 h-2.5" />}
                  {ep.auth_required ? "auth" : "public"}
                </span>
              )}
            </div>
            <p className="text-ink-ash text-xs leading-relaxed">{ep.description}</p>
            {ep.rate_limit && (
              <p className="text-ink-steel text-xs">Rate: {ep.rate_limit}</p>
            )}
            {ep.notes && (
              <p className="text-ink-steel text-xs italic">{ep.notes}</p>
            )}
            {/* Query params */}
            {ep.query_params && Object.keys(ep.query_params).length > 0 && (
              <div className="pt-1 border-t border-ink-graphite">
                <span className="text-ink-steel text-[10px] font-mono uppercase">Query params</span>
                <div className="mt-1 space-y-0.5">
                  {Object.entries(ep.query_params).map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-xs">
                      <span className="text-cyan-400 font-mono">{k}</span>
                      <span className="text-ink-steel">{v as string}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Error handling */}
      {data.error_handling && (
        <div className="bg-ink-charcoal border border-ink-graphite p-3">
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-1">Error Handling</h3>
          <p className="text-ink-ash text-xs leading-relaxed">{data.error_handling}</p>
        </div>
      )}
    </div>
  )
}

// ── Stack View ────────────────────────────────────────────────────────────────

function StackView({ data }: { data: StackData & Record<string, any> }) {
  const layers = data.layers ?? []
  const infra = data.infrastructure ?? null

  return (
    <div className="space-y-6">
      <h2 className="text-gold font-mono text-sm uppercase tracking-wider">Tech Stack</h2>

      {/* Philosophy */}
      {data.philosophy && (
        <p className="text-ink-ash text-xs italic leading-relaxed border-l-2 border-gold pl-3">
          {data.philosophy}
        </p>
      )}

      {/* Layer cards */}
      <div className="space-y-3">
        {layers.map((layer: any, i: number) => (
          <div key={i} className="bg-ink-charcoal border border-ink-graphite p-3 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-ink-steel text-xs font-mono uppercase">{layer.layer}</span>
              <span className="text-gold font-mono text-sm font-medium">{layer.primary}</span>
            </div>
            {layer.rationale && (
              <p className="text-ink-ash text-xs leading-relaxed">{layer.rationale}</p>
            )}
            {layer.alternatives?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                <span className="text-ink-steel text-[10px] mr-1">alt:</span>
                {layer.alternatives.map((alt: string) => (
                  <Badge key={alt} label={alt} />
                ))}
              </div>
            )}
            {layer.trade_off && (
              <p className="text-ink-steel text-xs italic">Trade-off: {layer.trade_off}</p>
            )}
          </div>
        ))}
      </div>

      {/* Infrastructure */}
      {infra && (
        <div>
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-2">Infrastructure</h3>
          <div className="space-y-1.5">
            {infra.deployment && (
              <div className="flex justify-between bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-ink-steel text-xs">Deployment</span>
                <span className="text-ink-white text-xs font-mono">{infra.deployment}</span>
              </div>
            )}
            {infra.ci_cd && (
              <div className="flex justify-between bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-ink-steel text-xs">CI/CD</span>
                <span className="text-ink-white text-xs font-mono">{infra.ci_cd}</span>
              </div>
            )}
            {infra.iac && (
              <div className="flex justify-between bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-ink-steel text-xs">IaC</span>
                <span className="text-ink-white text-xs font-mono">{infra.iac}</span>
              </div>
            )}
            {infra.observability?.length > 0 && (
              <div className="flex justify-between bg-ink-charcoal border border-ink-graphite px-3 py-2">
                <span className="text-ink-steel text-xs">Observability</span>
                <div className="flex gap-1">
                  {infra.observability.map((o: string) => <Badge key={o} label={o} />)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cost estimate */}
      {data.cost_estimate && (
        <div className="bg-ink-charcoal border border-ink-graphite p-3">
          <h3 className="text-ink-ash text-xs font-mono uppercase tracking-wider mb-1">Cost Estimate</h3>
          <p className="text-ink-ash text-xs leading-relaxed">{data.cost_estimate}</p>
        </div>
      )}
    </div>
  )
}
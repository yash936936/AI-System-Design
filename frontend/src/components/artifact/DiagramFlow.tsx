"use client"
import { useMemo, useState, useCallback } from "react"
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  Handle,
  ReactFlowProvider,
  type Node,
  type Edge,
  type NodeProps,
} from "reactflow"
import "reactflow/dist/style.css"
import {
  MonitorIcon,
  RouterIcon,
  ServerIcon,
  DatabaseIcon,
  ListOrderedIcon,
  ZapIcon as CacheIcon,
  CloudIcon,
  ShieldIcon,
  HardDriveIcon,
  PlugIcon,
  GlobeIcon,
  SparklesIcon,
  BoxIcon,
} from "lucide-react"
import type { ArchitectureData, ArchComponent } from "@/types"

// ── Layout ──────────────────────────────────────────────────────────────────
// No external layout library — components are placed in columns based on
// their deployment zone (if the model returned one) or, failing that, a
// sensible default left-to-right pipeline order by component type. Nodes
// in the same column are stacked vertically.

const TYPE_COLUMN: Record<string, number> = {
  client: 0,
  frontend: 0,
  cdn: 1,
  gateway: 1,
  auth: 2,
  backend: 2,
  ai: 2,
  cache: 3,
  queue: 3,
  database: 4,
  storage: 4,
  third_party: 5,
  external: 5,
}

const COL_WIDTH = 250
const ROW_HEIGHT = 130
const NODE_WIDTH = 210

function computeColumns(data: ArchitectureData): Record<string, number> {
  const zones = data.deployment_zones
  if (zones && zones.length > 0) {
    const colByComponent: Record<string, number> = {}
    zones.forEach((zone, zoneIdx) => {
      zone.components?.forEach((compId) => {
        colByComponent[compId] = zoneIdx
      })
    })
    // Components not covered by any zone fall back to type-based column
    data.components.forEach((c) => {
      if (colByComponent[c.id] === undefined) {
        colByComponent[c.id] = TYPE_COLUMN[c.type] ?? 2
      }
    })
    return colByComponent
  }

  const colByComponent: Record<string, number> = {}
  data.components.forEach((c) => {
    colByComponent[c.id] = TYPE_COLUMN[c.type] ?? 2
  })
  return colByComponent
}

function layout(data: ArchitectureData): Node<ArchComponent>[] {
  const columns = computeColumns(data)
  const rowCounter: Record<number, number> = {}

  return data.components.map((component) => {
    const col = columns[component.id] ?? 2
    const row = rowCounter[col] ?? 0
    rowCounter[col] = row + 1

    return {
      id: component.id,
      type: "archNode",
      position: { x: col * COL_WIDTH, y: row * ROW_HEIGHT },
      data: component,
    }
  })
}

function buildEdges(data: ArchitectureData): Edge[] {
  const componentIds = new Set(data.components.map((c) => c.id))

  if (data.data_flows && data.data_flows.length > 0) {
    return data.data_flows
      .filter((f) => componentIds.has(f.from) && componentIds.has(f.to))
      .map((flow, i) => ({
        id: `flow-${i}-${flow.from}-${flow.to}`,
        source: flow.from,
        target: flow.to,
        label: flow.label,
        animated: flow.protocol === "async" || flow.protocol === "WebSocket",
        style: { stroke: "#494949", strokeWidth: 1.5 },
        labelStyle: { fill: "#969696", fontSize: 10, fontFamily: "monospace" },
        labelBgStyle: { fill: "#000000", fillOpacity: 0.8 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#FFC000", width: 16, height: 16 },
      }))
  }

  // Fallback — derive edges from each component's `connections` list
  const seen = new Set<string>()
  const edges: Edge[] = []
  data.components.forEach((c) => {
    c.connections?.forEach((targetId) => {
      if (!componentIds.has(targetId)) return
      const key = `${c.id}->${targetId}`
      if (seen.has(key)) return
      seen.add(key)
      edges.push({
        id: key,
        source: c.id,
        target: targetId,
        style: { stroke: "#494949", strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#FFC000", width: 16, height: 16 },
      })
    })
  })
  return edges
}

// ── Custom node ───────────────────────────────────────────────────────────

const TYPE_ICON: Record<string, typeof BoxIcon> = {
  client: MonitorIcon,
  frontend: MonitorIcon,
  gateway: RouterIcon,
  cdn: GlobeIcon,
  backend: ServerIcon,
  auth: ShieldIcon,
  database: DatabaseIcon,
  storage: HardDriveIcon,
  queue: ListOrderedIcon,
  cache: CacheIcon,
  third_party: PlugIcon,
  external: CloudIcon,
  ai: SparklesIcon,
}

const TYPE_BORDER: Record<string, string> = {
  client: "border-blue-400",
  frontend: "border-blue-400",
  gateway: "border-teal-400",
  cdn: "border-gray-400",
  backend: "border-cyan-400",
  auth: "border-orange-400",
  database: "border-yellow-400",
  storage: "border-pink-400",
  queue: "border-purple-400",
  cache: "border-green-400",
  third_party: "border-indigo-400",
  external: "border-indigo-400",
  ai: "border-red-400",
}

const TYPE_TEXT: Record<string, string> = {
  client: "text-blue-400",
  frontend: "text-blue-400",
  gateway: "text-teal-400",
  cdn: "text-gray-400",
  backend: "text-cyan-400",
  auth: "text-orange-400",
  database: "text-yellow-400",
  storage: "text-pink-400",
  queue: "text-purple-400",
  cache: "text-green-400",
  third_party: "text-indigo-400",
  external: "text-indigo-400",
  ai: "text-red-400",
}

function ArchNode({ data, selected }: NodeProps<ArchComponent>) {
  const Icon = TYPE_ICON[data.type] ?? BoxIcon
  const borderClass = TYPE_BORDER[data.type] ?? "border-ink-graphite"
  const textClass = TYPE_TEXT[data.type] ?? "text-ink-steel"

  return (
    <div
      style={{ width: NODE_WIDTH }}
      className={`bg-ink-charcoal border ${selected ? "border-gold" : borderClass + "/50"} px-3 py-2.5 transition-colors`}
    >
      <Handle type="target" position={Position.Left} style={{ background: "#494949", border: "none", width: 6, height: 6 }} />
      <Handle type="source" position={Position.Right} style={{ background: "#494949", border: "none", width: 6, height: 6 }} />
      <div className="flex items-center gap-2">
        <Icon className={`w-3.5 h-3.5 shrink-0 ${textClass}`} />
        <span className="text-ink-white text-xs font-mono font-medium truncate">{data.name}</span>
      </div>
      {data.technology && (
        <p className="text-[10px] text-gold-text font-mono mt-1 truncate">{data.technology}</p>
      )}
    </div>
  )
}

const NODE_TYPES = { archNode: ArchNode }

// ── Detail drawer for the selected node ─────────────────────────────────────

function NodeDetail({ component, onClose }: { component: ArchComponent; onClose: () => void }) {
  const Icon = TYPE_ICON[component.type] ?? BoxIcon
  const textClass = TYPE_TEXT[component.type] ?? "text-ink-steel"

  return (
    <div className="border-t border-ink-graphite bg-ink-charcoal p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${textClass}`} />
          <span className="text-ink-white text-sm font-mono font-medium">{component.name}</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 bg-ink-graphite text-ink-steel">{component.type}</span>
        </div>
        <button onClick={onClose} className="text-ink-steel hover:text-ink-white text-xs font-mono">
          close
        </button>
      </div>
      <p className="text-ink-ash text-xs leading-relaxed">{component.description}</p>
      {component.responsibilities?.length > 0 && (
        <ul className="space-y-0.5">
          {component.responsibilities.map((r, i) => (
            <li key={i} className="text-ink-steel text-xs flex gap-1">
              <span className="text-gold shrink-0">·</span> {r}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────

interface DiagramFlowProps {
  data: ArchitectureData
}

function DiagramFlowInner({ data }: DiagramFlowProps) {
  const nodes = useMemo(() => layout(data), [data])
  const edges = useMemo(() => buildEdges(data), [data])
  const [selected, setSelected] = useState<ArchComponent | null>(null)

  const handleNodeClick = useCallback((_: unknown, node: Node<ArchComponent>) => {
    setSelected(node.data)
  }, [])

  return (
    <div className="border border-ink-graphite bg-surface-black">
      <div style={{ height: 360 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodeClick={handleNodeClick}
          onPaneClick={() => setSelected(null)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.3}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#313131" />
          <Controls showInteractive={false} className="!bg-ink-charcoal !border !border-ink-graphite [&>button]:!bg-ink-charcoal [&>button]:!border-ink-graphite [&>button]:!text-ink-steel [&>button:hover]:!bg-ink-graphite" />
          <MiniMap
            pannable
            zoomable
            maskColor="rgba(0,0,0,0.75)"
            nodeColor="#494949"
            style={{ backgroundColor: "#0a0a0a" }}
          />
        </ReactFlow>
      </div>
      {selected && <NodeDetail component={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

export default function DiagramFlow({ data }: DiagramFlowProps) {
  if (!data.components || data.components.length === 0) return null
  return (
    <ReactFlowProvider>
      <DiagramFlowInner data={data} />
    </ReactFlowProvider>
  )
}

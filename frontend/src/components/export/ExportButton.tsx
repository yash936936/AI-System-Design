// frontend/src/components/export/ExportButton.tsx
"use client"

import { useState } from "react"
import { Download, FileText, FileJson, File, ChevronDownIcon } from "lucide-react"
import { useStore } from "@/store/useStore"

type Format = "md" | "json" | "pdf"

const FORMAT_OPTIONS: { fmt: Format; label: string; Icon: React.ElementType }[] = [
  { fmt: "md", label: "Markdown", Icon: FileText },
  { fmt: "json", label: "JSON", Icon: FileJson },
  { fmt: "pdf", label: "PDF (print)", Icon: File },
]

function buildMarkdown(artifact: any, sessionPrompt: string): string {
  const lines: string[] = []
  lines.push(`# System Design: ${sessionPrompt}`)
  lines.push("")

  if (artifact.diagram) {
    lines.push("## Architecture Components")
    lines.push("")
    const d = artifact.diagram
    d.components?.forEach((c: any) => {
      lines.push(`### ${c.name} (${c.type})`)
      if (c.technology) lines.push(`**Technology:** ${c.technology}`)
      if (c.description) lines.push(c.description)
      if (c.responsibilities?.length) {
        lines.push("")
        c.responsibilities.forEach((r: string) => lines.push(`- ${r}`))
      }
      lines.push("")
    })
    if (d.data_flows?.length) {
      lines.push("### Data Flows")
      d.data_flows.forEach((f: any) => lines.push(`- ${f.from} → ${f.to}${f.label ? `: ${f.label}` : ""}`))
      lines.push("")
    }
    if (d.key_design_decisions?.length) {
      lines.push("### Key Decisions")
      d.key_design_decisions.forEach((dec: string, i: number) => lines.push(`${i + 1}. ${dec}`))
      lines.push("")
    }
  }

  if (artifact.capacity) {
    const c = artifact.capacity
    lines.push("## Capacity Estimation")
    lines.push("")
    if (c.dau) lines.push(`- **Daily Active Users:** ${c.dau.toLocaleString()}`)
    if (c.peak_read_qps) lines.push(`- **Peak Read QPS:** ${c.peak_read_qps} req/s`)
    if (c.peak_write_qps) lines.push(`- **Peak Write QPS:** ${c.peak_write_qps} req/s`)
    if (c.daily_storage_gb) lines.push(`- **Daily Storage:** ${c.daily_storage_gb} GB`)
    if (c.five_year_storage_tb) lines.push(`- **5-Year Storage:** ${c.five_year_storage_tb} TB`)
    if (c.bandwidth_gbps) lines.push(`- **Bandwidth:** ${c.bandwidth_gbps} Gbps`)
    if (c.scaling_notes) { lines.push(""); lines.push(`**Scaling Notes:** ${c.scaling_notes}`) }
    lines.push("")
  }

  if (artifact.data_model) {
    const dm = artifact.data_model
    lines.push("## Data Model")
    lines.push("")
    if (dm.decision) lines.push(`**Decision:** ${dm.decision}`)
    if (dm.rationale) lines.push(dm.rationale)
    lines.push("")
    dm.entities?.forEach((e: any) => {
      lines.push(`### ${e.name}${e.store ? ` (${e.store})` : ""}`)
      lines.push("")
      lines.push("| Column | Type | Flags |")
      lines.push("|--------|------|-------|")
      e.columns?.forEach((col: any) => {
        const flags = [col.primary && "PK", col.indexed && "IDX", col.nullable === false && "NOT NULL"].filter(Boolean).join(", ")
        lines.push(`| ${col.name} | ${col.type} | ${flags} |`)
      })
      lines.push("")
    })
  }

  if (artifact.api) {
    const a = artifact.api
    lines.push("## API Design")
    lines.push("")
    if (a.style) lines.push(`**Style:** ${a.style}`)
    if (a.auth) lines.push(`**Auth:** ${a.auth}`)
    lines.push("")
    a.endpoints?.forEach((ep: any) => {
      lines.push(`### ${ep.method} ${ep.path}`)
      if (ep.description) lines.push(ep.description)
      if (ep.auth_required != null) lines.push(`Auth required: ${ep.auth_required}`)
      lines.push("")
    })
  }

  if (artifact.stack) {
    const s = artifact.stack
    lines.push("## Tech Stack")
    lines.push("")
    if (s.philosophy) lines.push(`> ${s.philosophy}`)
    lines.push("")
    s.layers?.forEach((layer: any) => {
      lines.push(`- **${layer.layer}:** ${layer.primary}`)
      if (layer.rationale) lines.push(`  ${layer.rationale}`)
    })
    lines.push("")
  }

  return lines.join("\n")
}

export default function ExportButton({ className = "" }: { className?: string }) {
  const { artifact, session } = useStore()
  const [open, setOpen] = useState(false)
  const [exporting, setExporting] = useState(false)

  const hasData = artifact.diagram || artifact.capacity || artifact.data_model || artifact.api || artifact.stack

  const handleExport = async (fmt: Format) => {
    if (exporting || !hasData) return
    setExporting(true)
    setOpen(false)

    try {
      const prompt = session.prompt || "System Design"
      const filename = `system-design-${Date.now()}`

      if (fmt === "json") {
        const data = {
          prompt,
          generated_at: new Date().toISOString(),
          diagram: artifact.diagram,
          capacity: artifact.capacity,
          data_model: artifact.data_model,
          api: artifact.api,
          stack: artifact.stack,
        }
        triggerDownload(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), `${filename}.json`)
      } else if (fmt === "md") {
        const md = buildMarkdown(artifact, prompt)
        triggerDownload(new Blob([md], { type: "text/markdown" }), `${filename}.md`)
      } else if (fmt === "pdf") {
        window.print()
      }
    } finally {
      setExporting(false)
    }
  }

  function triggerDownload(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!hasData) return null

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={exporting}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-gold text-surface-black text-xs font-lambo tracking-wider uppercase hover:bg-gold-dark disabled:opacity-50 transition-colors"
      >
        <Download size={12} strokeWidth={2.5} />
        {exporting ? "Exporting…" : "Export"}
        <ChevronDownIcon size={11} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div
            className="absolute right-0 top-full mt-1 z-20 border shadow-xl overflow-hidden min-w-[140px]"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-default)" }}
          >
            {FORMAT_OPTIONS.map(({ fmt, label, Icon }) => (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="flex items-center gap-2 w-full px-4 py-2.5 text-xs font-lambo tracking-wider uppercase transition-colors"
                style={{ color: "var(--text-secondary)" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#FFC000" }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)" }}
              >
                <Icon size={13} />
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
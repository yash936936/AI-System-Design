// frontend/src/components/export/ArtifactExportDocument.tsx
"use client"

import { createPortal } from "react-dom"
import { useEffect, useState } from "react"
import { useStore } from "@/store/useStore"

/**
 * Renders a hidden, print-only document containing ALL FIVE artifact tabs
 * (Diagram, Capacity, Data Model, API, Stack) combined into a single,
 * clean, light-on-white static layout — independent of the app's current
 * theme or which tab happens to be active on screen.
 *
 * It is portaled directly onto <body> so the print stylesheet
 * (`#artifact-export-print` rules in globals.css) can reliably hide every
 * other element on the page and print *only* this document when the user
 * chooses "PDF (print)" from the Export menu — instead of printing the
 * whole app screen.
 */
export default function ArtifactExportDocument() {
  const { artifact, session } = useStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])
  if (!mounted) return null

  const hasData = artifact.diagram || artifact.capacity || artifact.data_model || artifact.api || artifact.stack
  if (!hasData) return null

  return createPortal(
    <div id="artifact-export-print">
      <ExportDoc artifact={artifact} prompt={session.prompt || "System Design"} />
    </div>,
    document.body
  )
}

// ── Shared static styles (kept inline so the export doc renders the same
//    regardless of which Tailwind theme overrides are active on screen) ──
const styles = {
  page: { background: "#FFFFFF", color: "#111111", fontFamily: "'Oswald', 'Helvetica Neue', Arial, sans-serif", padding: "32px", maxWidth: "850px", margin: "0 auto" },
  h1: { fontSize: "22px", fontWeight: 600, marginBottom: "4px", color: "#111111" },
  meta: { fontSize: "11px", color: "#666666", marginBottom: "28px" },
  h2: { fontSize: "15px", fontWeight: 600, textTransform: "uppercase" as const, letterSpacing: "0.04em", color: "#946B00", borderBottom: "2px solid #946B00", paddingBottom: "4px", marginTop: "32px", marginBottom: "12px", pageBreakAfter: "avoid" as const },
  h3: { fontSize: "12.5px", fontWeight: 600, color: "#111111", marginTop: "14px", marginBottom: "4px" },
  p: { fontSize: "11.5px", lineHeight: 1.5, color: "#333333", margin: "2px 0 6px" },
  card: { border: "1px solid #DDDDDD", borderRadius: "3px", padding: "10px 12px", marginBottom: "8px", pageBreakInside: "avoid" as const, background: "#FAFAFA" },
  badge: { display: "inline-block", fontSize: "9.5px", fontFamily: "monospace", color: "#444444", background: "#EAEAEA", border: "1px solid #D5D5D5", borderRadius: "2px", padding: "1px 6px", marginRight: "4px" },
  table: { width: "100%", fontSize: "11px", borderCollapse: "collapse" as const, marginBottom: "10px" },
  th: { textAlign: "left" as const, fontSize: "10px", textTransform: "uppercase" as const, color: "#666666", borderBottom: "1px solid #CCCCCC", padding: "4px 6px" },
  td: { borderBottom: "1px solid #EEEEEE", padding: "4px 6px", color: "#222222" },
  li: { fontSize: "11.5px", color: "#333333", marginBottom: "2px" },
  mono: { fontFamily: "monospace" as const },
}

function stripMarkdown(text: string): string {
  return (text ?? "").replace(/\*\*/g, "")
}

function ExportDoc({ artifact, prompt }: { artifact: any; prompt: string }) {
  return (
    <div style={styles.page}>
      <h1 style={styles.h1}>System Design: {prompt}</h1>
      <p style={styles.meta}>Generated {new Date().toLocaleString()} · All artifact sections combined into a single export</p>

      {artifact.diagram && <DiagramSection data={artifact.diagram} />}
      {artifact.capacity && <CapacitySection data={artifact.capacity} />}
      {artifact.data_model && <DataModelSection data={artifact.data_model} />}
      {artifact.api && <ApiSection data={artifact.api} />}
      {artifact.stack && <StackSection data={artifact.stack} />}
    </div>
  )
}

// ── Diagram ──────────────────────────────────────────────────────────────
function DiagramSection({ data }: { data: any }) {
  const components = data.components ?? []
  const flows = data.data_flows ?? []
  const zones = data.deployment_zones ?? []
  const decisions = data.key_design_decisions ?? []

  return (
    <section>
      <h2 style={styles.h2}>Architecture Diagram</h2>
      {components.map((c: any) => (
        <div key={c.id} style={styles.card}>
          <div>
            <strong style={{ fontSize: "12px" }}>{c.name}</strong>{" "}
            <span style={styles.badge}>{c.type}</span>
            {c.technology && <span style={styles.badge}>{c.technology}</span>}
          </div>
          {c.description && <p style={styles.p}>{c.description}</p>}
          {c.responsibilities?.length > 0 && (
            <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
              {c.responsibilities.map((r: string, i: number) => <li key={i} style={styles.li}>{r}</li>)}
            </ul>
          )}
          {c.connections?.length > 0 && (
            <p style={{ ...styles.p, marginTop: "6px" }}>
              {c.connections.map((conn: string) => <span key={conn} style={styles.badge}>→ {conn}</span>)}
            </p>
          )}
        </div>
      ))}

      {flows.length > 0 && (
        <>
          <h3 style={styles.h3}>Data Flows</h3>
          {flows.map((f: any, i: number) => (
            <p key={i} style={styles.p}>
              <span style={styles.mono}>{f.from}</span> → <span style={styles.mono}>{f.to}</span>
              {f.label ? ` — ${f.label}` : ""}{f.protocol ? `  [${f.protocol}]` : ""}
            </p>
          ))}
        </>
      )}

      {zones.length > 0 && (
        <>
          <h3 style={styles.h3}>Deployment Zones</h3>
          {zones.map((z: any, i: number) => (
            <p key={i} style={styles.p}><strong>{z.zone}:</strong> {z.components?.join(", ")}</p>
          ))}
        </>
      )}

      {decisions.length > 0 && (
        <>
          <h3 style={styles.h3}>Key Design Decisions</h3>
          <ol style={{ margin: "0 0 0 16px", padding: 0 }}>
            {decisions.map((d: string, i: number) => <li key={i} style={styles.li}>{stripMarkdown(d)}</li>)}
          </ol>
        </>
      )}
    </section>
  )
}

// ── Capacity ─────────────────────────────────────────────────────────────
function CapacitySection({ data }: { data: any }) {
  const rows: [string, string][] = [
    ["Daily Active Users", data.dau?.toLocaleString()],
    ["Peak Read QPS", data.peak_read_qps != null ? `${data.peak_read_qps} req/s` : undefined],
    ["Peak Write QPS", data.peak_write_qps != null ? `${data.peak_write_qps} req/s` : undefined],
    ["Daily Storage", data.daily_storage_gb != null ? `${data.daily_storage_gb} GB` : undefined],
    ["5-Year Storage", data.five_year_storage_tb != null ? `${data.five_year_storage_tb} TB` : undefined],
    ["Bandwidth", data.bandwidth_gbps != null ? `${data.bandwidth_gbps} Gbps` : undefined],
  ].filter(([, v]) => v != null) as [string, string][]

  return (
    <section>
      <h2 style={styles.h2}>Capacity Estimation</h2>
      <table style={styles.table}>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <td style={{ ...styles.td, fontWeight: 600 }}>{label}</td>
              <td style={styles.td}>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.scaling_notes && <p style={styles.p}>{data.scaling_notes}</p>}
    </section>
  )
}

// ── Data Model ───────────────────────────────────────────────────────────
function DataModelSection({ data }: { data: any }) {
  const entities = data.entities ?? []
  return (
    <section>
      <h2 style={styles.h2}>Data Model</h2>
      {data.decision && <p style={styles.p}><strong>Decision:</strong> {data.decision}</p>}
      {data.rationale && <p style={styles.p}>{data.rationale}</p>}
      {entities.map((e: any, i: number) => (
        <div key={i} style={styles.card}>
          <strong style={{ fontSize: "12px" }}>{e.name}</strong>{e.store ? <span style={styles.badge}>{e.store}</span> : null}
          {e.columns?.length > 0 && (
            <table style={styles.table}>
              <thead>
                <tr><th style={styles.th}>Column</th><th style={styles.th}>Type</th><th style={styles.th}>Flags</th></tr>
              </thead>
              <tbody>
                {e.columns.map((col: any, j: number) => {
                  const flags = [col.primary && "PK", col.indexed && "IDX", col.nullable === false && "NOT NULL"].filter(Boolean).join(", ")
                  return (
                    <tr key={j}>
                      <td style={{ ...styles.td, ...styles.mono }}>{col.name}</td>
                      <td style={styles.td}>{col.type}</td>
                      <td style={styles.td}>{flags}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
          {e.partition_strategy && <p style={styles.p}>{e.partition_strategy}</p>}
          {e.access_patterns?.length > 0 && (
            <p>{e.access_patterns.map((p: string) => <span key={p} style={styles.badge}>{p}</span>)}</p>
          )}
        </div>
      ))}
      {data.caching_strategy && <p style={styles.p}><strong>Caching Strategy:</strong> {data.caching_strategy}</p>}
      {data.notes && <p style={{ ...styles.p, fontStyle: "italic" }}>{data.notes}</p>}
    </section>
  )
}

// ── API ──────────────────────────────────────────────────────────────────
function ApiSection({ data }: { data: any }) {
  const endpoints = data.endpoints ?? []
  return (
    <section>
      <h2 style={styles.h2}>API Design</h2>
      <p style={styles.p}>
        {data.style && <><strong>Style:</strong> {data.style}  </>}
        {data.auth && <><strong>Auth:</strong> {data.auth}  </>}
        {data.versioning && <><strong>Versioning:</strong> {data.versioning}</>}
      </p>
      {data.rate_limiting && <p style={styles.p}><strong>Rate Limiting:</strong> {data.rate_limiting}</p>}
      {endpoints.map((ep: any, i: number) => (
        <div key={i} style={styles.card}>
          <span style={{ ...styles.mono, fontWeight: 700, fontSize: "11.5px" }}>{ep.method}</span>{" "}
          <span style={styles.mono}>{ep.path}</span>{" "}
          {ep.auth_required != null && <span style={styles.badge}>{ep.auth_required ? "auth" : "public"}</span>}
          {ep.description && <p style={styles.p}>{ep.description}</p>}
          {ep.rate_limit && <p style={styles.p}>Rate: {ep.rate_limit}</p>}
          {ep.query_params && Object.keys(ep.query_params).length > 0 && (
            <p style={styles.p}>
              {Object.entries(ep.query_params).map(([k, v]) => <span key={k}><span style={styles.mono}>{k}</span>: {v as string}  </span>)}
            </p>
          )}
        </div>
      ))}
      {data.error_handling && <p style={styles.p}><strong>Error Handling:</strong> {data.error_handling}</p>}
    </section>
  )
}

// ── Stack ────────────────────────────────────────────────────────────────
function StackSection({ data }: { data: any }) {
  const layers = data.layers ?? []
  const infra = data.infrastructure ?? null
  return (
    <section>
      <h2 style={styles.h2}>Tech Stack</h2>
      {data.philosophy && <p style={{ ...styles.p, fontStyle: "italic" }}>{data.philosophy}</p>}
      {layers.map((layer: any, i: number) => (
        <div key={i} style={styles.card}>
          <span style={styles.badge}>{layer.layer}</span>{" "}
          <strong style={{ fontSize: "12px" }}>{layer.primary}</strong>
          {layer.rationale && <p style={styles.p}>{layer.rationale}</p>}
          {layer.alternatives?.length > 0 && (
            <p style={styles.p}>alt: {layer.alternatives.map((a: string) => <span key={a} style={styles.badge}>{a}</span>)}</p>
          )}
          {layer.trade_off && <p style={{ ...styles.p, fontStyle: "italic" }}>Trade-off: {layer.trade_off}</p>}
        </div>
      ))}
      {infra && (
        <>
          <h3 style={styles.h3}>Infrastructure</h3>
          <table style={styles.table}>
            <tbody>
              {infra.deployment && <tr><td style={{ ...styles.td, fontWeight: 600 }}>Deployment</td><td style={styles.td}>{infra.deployment}</td></tr>}
              {infra.ci_cd && <tr><td style={{ ...styles.td, fontWeight: 600 }}>CI/CD</td><td style={styles.td}>{infra.ci_cd}</td></tr>}
              {infra.iac && <tr><td style={{ ...styles.td, fontWeight: 600 }}>IaC</td><td style={styles.td}>{infra.iac}</td></tr>}
              {infra.observability?.length > 0 && <tr><td style={{ ...styles.td, fontWeight: 600 }}>Observability</td><td style={styles.td}>{infra.observability.join(", ")}</td></tr>}
            </tbody>
          </table>
        </>
      )}
      {data.cost_estimate && <p style={styles.p}><strong>Cost Estimate:</strong> {data.cost_estimate}</p>}
    </section>
  )
}
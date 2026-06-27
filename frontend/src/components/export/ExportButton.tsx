"use client"

import { useState } from "react"
import { Download, FileText, FileJson, File } from "lucide-react"
import { createExport, type ExportRequest } from "@/lib/api"
import { useAuth } from "@/hooks/useAuth"

interface Props {
  sessionId: string
  sections?: string[]
  className?: string
}

type Format = "md" | "json" | "pdf"

const FORMAT_OPTIONS: { fmt: Format; label: string; Icon: React.ElementType }[] = [
  { fmt: "md", label: "Markdown", Icon: FileText },
  { fmt: "json", label: "JSON", Icon: FileJson },
  { fmt: "pdf", label: "PDF", Icon: File },
]

export default function ExportButton({ sessionId, sections, className = "" }: Props) {
  const { isAuthenticated } = useAuth()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState<Format | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async (fmt: Format) => {
    if (loading) return
    setError(null)
    setLoading(fmt)
    setOpen(false)

    try {
      const result = await createExport(sessionId, {
        format: fmt,
        sections: sections ?? [],
      } satisfies ExportRequest)

      // Open the download URL in a new tab
      window.open(result.download_url, "_blank", "noopener,noreferrer")
    } catch (err: any) {
      setError(err?.message ?? "Export failed")
    } finally {
      setLoading(null)
    }
  }

  if (!isAuthenticated) return null

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={loading !== null}
        className="
          flex items-center gap-2 px-3 py-1.5
          bg-gold text-surface-black
          text-xs font-lambo tracking-wider uppercase
          hover:bg-gold-dark
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors
        "
      >
        <Download size={13} strokeWidth={2.5} />
        {loading ? `Exporting ${loading.toUpperCase()}…` : "Export"}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 bg-surface-charcoal border border-ink-shadow rounded-sm shadow-xl overflow-hidden min-w-[140px]">
            {FORMAT_OPTIONS.map(({ fmt, label, Icon }) => (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="flex items-center gap-2 w-full px-4 py-2.5 text-xs font-lambo tracking-wider uppercase text-ink-smoke hover:bg-surface-iron hover:text-gold transition-colors"
              >
                <Icon size={13} />
                {label}
              </button>
            ))}
          </div>
        </>
      )}

      {error && (
        <p className="absolute top-full mt-1 right-0 text-[10px] text-red-400 whitespace-nowrap">
          {error}
        </p>
      )}
    </div>
  )
}
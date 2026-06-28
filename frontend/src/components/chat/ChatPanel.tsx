// frontend/src/components/chat/ChatPanel.tsx
"use client"
import { useRef, useEffect, useState, useCallback } from "react"
import { SendHorizontalIcon, ZapIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import { classifyPrompt, getMCQTemplate, createSession, openStream } from "@/lib/api"
import ChatMessageItem from "./ChatMessage"
import { LogoMark } from "@/components/brand/Logo"
import type { SSEEvent } from "@/types"

const EXAMPLE_PROMPTS = [
  "Design a URL shortener like Bit.ly",
  "Design Twitter's timeline feed",
  "Design WhatsApp's messaging layer",
  "Design Netflix's video streaming service",
  "Design Uber's ride-matching system",
  "Design a rate limiter",
]

export default function ChatPanel() {
  const {
    session, messages, addMessage, startSession, setClassification, setMcqTemplate,
    setSessionId, setSessionStatus, handleSSEEvent, handleStreamDone, handleStreamError,
  } = useStore()

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const streamCleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  useEffect(() => { return () => { streamCleanupRef.current?.() } }, [])

  const handleSubmit = async () => {
    const prompt = input.trim()
    if (!prompt || isLoading) return
    setInput("")
    setIsLoading(true)
    startSession(prompt)
    try {
      const classification = await classifyPrompt(prompt)
      setClassification(classification)
      const template = await getMCQTemplate(classification.type)
      setMcqTemplate(template)
    } catch (err) {
      addMessage("assistant", "text", `Something went wrong: ${(err as Error).message}. Please try again.`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerate = useCallback(async () => {
    if (!session.designType || session.status !== "creating") return
    setIsLoading(true)
    try {
      const result = await createSession({ prompt: session.prompt, design_type: session.designType, context: session.context })
      setSessionId(result.session_id)
      addMessage("assistant", "status", "Session created. Running RAG retrieval…", { icon: "search" })
      setSessionStatus("retrieving")
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        await fetch(`${apiBase}/api/sessions/${result.session_id}/retrieve`, { method: "GET", headers: { Accept: "application/json" } })
      } catch (ragErr) {
        console.warn("RAG retrieval request failed (non-fatal):", ragErr)
      }
      addMessage("assistant", "status", "Retrieval complete. Starting generation pipeline…", { icon: "rocket" })
      setSessionStatus("generating")
      const cleanup = openStream(result.session_id, {
        onEvent: (event: SSEEvent) => handleSSEEvent(event),
        onDone: () => handleStreamDone(),
        onError: (err: string, errorCode?: string) => handleStreamError(err, errorCode),
      })
      streamCleanupRef.current = cleanup
    } catch (err) {
      addMessage("assistant", "text", `Failed to start generation: ${(err as Error).message}`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }, [session.designType, session.status, session.prompt, session.context,
      setSessionId, setSessionStatus, addMessage, handleSSEEvent, handleStreamDone, handleStreamError])

  const isEmpty = messages.length === 0
  const isGenerating = session.status === "generating"
  const inputDisabled = isLoading || isGenerating

  return (
    <div className="flex-1 flex flex-col h-full bg-ink-black">
      <div className="flex-1 overflow-y-auto px-4 py-6">

        {isEmpty && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
            <div className="w-12 h-12 border-2 border-gold mb-5 flex items-center justify-center">
              <LogoMark size={24} className="text-gold" />
            </div>
            <h1 className="text-ink-white text-xl font-light mb-2 uppercase tracking-wide">
              What System Do You Want To Design?
            </h1>
            <p className="text-ink-steel text-xs mb-6 leading-relaxed">
              Describe a product or component and I'll guide you through HLD or LLD — with real-world references.
            </p>
            <div className="flex flex-wrap gap-1.5 justify-center">
              {EXAMPLE_PROMPTS.map((p) => (
                <button key={p} onClick={() => setInput(p)} className="btn-ghost text-btnsm py-2 px-3 text-xs">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg) => (
            <ChatMessageItem key={msg.id} message={msg} mcqTemplate={session.mcqTemplate} />
          ))}
        </div>

        {session.status === "creating" && (
          <div className="flex justify-center mt-5">
            <button onClick={handleGenerate} disabled={isLoading} className="btn-accent flex items-center gap-2 disabled:opacity-50">
              <ZapIcon className="w-4 h-4" />
              Generate Design
            </button>
          </div>
        )}

        {session.status === "retrieving" && (
          <div className="flex items-center gap-2 text-ink-steel text-xs mt-3">
            <div className="flex gap-1">
              {[0,1,2].map((i) => <div key={i} className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" style={{ animationDelay: `${i*150}ms` }} />)}
            </div>
            Retrieving reference designs…
          </div>
        )}

        {isGenerating && (
          <div className="flex items-center gap-2 text-ink-steel text-xs mt-3">
            <div className="flex gap-1">
              {[0,1,2].map((i) => <div key={i} className="w-1 h-1 bg-gold rounded-full animate-pulse" style={{ animationDelay: `${i*150}ms` }} />)}
            </div>
            Generating design sections…
          </div>
        )}

        {isLoading && !isGenerating && session.status !== "retrieving" && (
          <div className="flex items-center gap-2 text-ink-steel text-xs mt-3">
            <div className="flex gap-1">
              {[0,1,2].map((i) => <div key={i} className="w-1 h-1 bg-gold rounded-full animate-pulse" style={{ animationDelay: `${i*150}ms` }} />)}
            </div>
            Processing…
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t border-ink-graphite p-3">
        <div className="max-w-2xl mx-auto flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit() } }}
            placeholder="Describe the system you want to design…"
            className="input-dark flex-1 py-2.5 px-3 text-xs resize-none min-h-[44px] max-h-[140px]"
            rows={1}
            disabled={inputDisabled}
          />
          <button onClick={handleSubmit} disabled={!input.trim() || inputDisabled} className="btn-accent-icon p-2.5">
            <SendHorizontalIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
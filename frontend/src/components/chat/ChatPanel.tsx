"use client"
import { useRef, useEffect, useState, useCallback } from "react"
import { SendHorizontalIcon, ZapIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import { classifyPrompt, getMCQTemplate, createSession, openStream } from "@/lib/api"
import ChatMessageItem from "./ChatMessage"
import type { SSEEvent } from "@/types"

const EXAMPLE_PROMPTS = [
  "Design Twitter's timeline feed",
  "Design the auth service for a SaaS app",
  "How would you design WhatsApp's messaging layer?",
  "LLD for a distributed rate limiter",
]

export default function ChatPanel() {
  const {
    session,
    messages,
    addMessage,
    startSession,
    setClassification,
    setMcqTemplate,
    setSessionId,
    setSessionStatus,
    handleSSEEvent,
    handleStreamDone,
    handleStreamError,
  } = useStore()

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  // Holds the cleanup fn returned by openStream so we can abort on unmount
  const streamCleanupRef = useRef<(() => void) | null>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  // Cleanup stream on unmount
  useEffect(() => {
    return () => {
      streamCleanupRef.current?.()
    }
  }, [])

  // ── Phase A + B ────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    const prompt = input.trim()
    if (!prompt || isLoading) return
    setInput("")
    setIsLoading(true)

    startSession(prompt)

    try {
      // Phase A: Classify
      const classification = await classifyPrompt(prompt)
      setClassification(classification)

      // Phase B: Fetch MCQ template
      const template = await getMCQTemplate(classification.type)
      setMcqTemplate(template)
    } catch (err) {
      addMessage(
        "assistant",
        "text",
        `Something went wrong: ${(err as Error).message}. Please try again.`,
      )
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  // ── Phase C + D ────────────────────────────────────────────────────────────
  // Called when the user clicks "Generate Design".
  // Flow: createSession → retrieve (Phase C) → openStream (Phase D)
  const handleGenerate = useCallback(async () => {
    if (!session.designType || session.status !== "creating") return
    setIsLoading(true)

    try {
      // Step 1: Create session in the backend
      const result = await createSession({
        prompt: session.prompt,
        design_type: session.designType,
        context: session.context,
      })
      setSessionId(result.session_id)

      addMessage("assistant", "text", "Session created. Running RAG retrieval… 🔍")
      setSessionStatus("retrieving")

      // Step 2: Phase C — trigger RAG retrieval so chunks are stored in the DB
      // before the generation stream starts. The generation service loads them
      // from the DB at stream-start time, so this must complete first.
      // We fire-and-forget any error here; generation has a graceful empty-chunk fallback.
      try {
        const apiBase =
          process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        await fetch(
          `${apiBase}/api/sessions/${result.session_id}/retrieve`,
          { method: "GET", headers: { Accept: "application/json" } },
        )
      } catch (ragErr) {
        // Non-fatal — generation will proceed with empty chunks
        console.warn("RAG retrieval request failed (non-fatal):", ragErr)
      }

      addMessage(
        "assistant",
        "text",
        "Retrieval complete. Starting generation pipeline… 🚀",
      )
      setSessionStatus("generating")

      // Step 3: Phase D — open SSE stream
      const cleanup = openStream(result.session_id, {
        onEvent: (event: SSEEvent) => handleSSEEvent(event),
        onDone: () => handleStreamDone(),
        onError: (err: string, errorCode?: string) =>
          handleStreamError(err, errorCode),
      })
      streamCleanupRef.current = cleanup
    } catch (err) {
      addMessage(
        "assistant",
        "text",
        `Failed to start generation: ${(err as Error).message}`,
      )
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }, [
    session.designType,
    session.status,
    session.prompt,
    session.context,
    setSessionId,
    setSessionStatus,
    addMessage,
    handleSSEEvent,
    handleStreamDone,
    handleStreamError,
  ])

  const isEmpty = messages.length === 0
  const isGenerating = session.status === "generating"
  const inputDisabled = isLoading || isGenerating

  return (
    <div className="flex-1 flex flex-col h-full bg-ink-black">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {/* Empty state */}
        {isEmpty && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto">
            <div className="w-16 h-16 border-2 border-gold mb-6 flex items-center justify-center">
              <span className="text-gold font-mono text-2xl">S</span>
            </div>
            <h1 className="text-ink-white text-3xl font-light mb-3">
              What System Do You Want To Design?
            </h1>
            <p className="text-ink-steel text-sm mb-8">
              Describe a product or component and I'll guide you through HLD or
              LLD — with real-world references.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {EXAMPLE_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => setInput(p)}
                  className="btn-ghost text-btnsm"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((msg) => (
          <ChatMessageItem
            key={msg.id}
            message={msg}
            mcqTemplate={session.mcqTemplate}
          />
        ))}

        {/* Generate Design button — shown when all MCQs are complete */}
        {session.status === "creating" && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleGenerate}
              disabled={isLoading}
              className="btn-gold flex items-center gap-2 disabled:opacity-50"
            >
              <ZapIcon className="w-4 h-4" />
              Generate Design
            </button>
          </div>
        )}

        {/* Retrieving indicator */}
        {session.status === "retrieving" && (
          <div className="flex items-center gap-2 text-ink-steel text-sm mt-4">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
            Retrieving reference designs…
          </div>
        )}

        {/* Generating indicator */}
        {isGenerating && (
          <div className="flex items-center gap-2 text-ink-steel text-sm mt-4">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 bg-gold rounded-full animate-pulse"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
            Generating design sections…
          </div>
        )}

        {/* Generic loading indicator (classify / MCQ fetch) */}
        {isLoading && !isGenerating && session.status !== "retrieving" && (
          <div className="flex items-center gap-2 text-ink-steel text-sm mt-4">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 bg-gold rounded-full animate-pulse"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
            Processing…
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-ink-graphite p-4">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            placeholder="Describe the system you want to design…"
            className="input-dark flex-1 py-3 px-4 text-sm resize-none min-h-[48px] max-h-[160px]"
            rows={1}
            disabled={inputDisabled}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || inputDisabled}
            className="btn-gold p-3 disabled:opacity-40"
          >
            <SendHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
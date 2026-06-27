"use client"
import { useRef, useEffect, useState } from "react"
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
    session, messages, addMessage,
    startSession, setClassification, setMcqTemplate, setSessionId,
    setSessionStatus, handleSSEEvent, handleStreamDone, handleStreamError,
  } = useStore()

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
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
      addMessage("assistant", "text", `Something went wrong: ${(err as Error).message}. Please try again.`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  // Phase D: Generate design with SSE streaming
  const handleGenerate = async () => {
    if (!session.designType || session.status !== "creating") return
    setIsLoading(true)
    setSessionStatus("creating")

    try {
      // Create session
      const result = await createSession({
        prompt: session.prompt,
        design_type: session.designType,
        context: session.context,
      })
      setSessionId(result.session_id)
      
      addMessage("assistant", "text",
        "Session created. Starting generation pipeline… 🚀"
      )
      setSessionStatus("generating")

      // Open SSE stream
     const cleanup = openStream(
          result.session_id,
      {
       onEvent: (event: SSEEvent) => handleSSEEvent(event),
       onDone: () => handleStreamDone(),
        onError: (err: string, errorCode?: string) => handleStreamError(err, errorCode),
    }
)
streamCleanupRef.current = cleanup

    } catch (err) {
      addMessage("assistant", "text", `Failed to create session: ${(err as Error).message}`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  const isEmpty = messages.length === 0

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
              Describe a product or component and I'll guide you through HLD or LLD — with real-world references.
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
          <ChatMessageItem key={msg.id} message={msg} mcqTemplate={session.mcqTemplate} />
        ))}

        {/* Generate button */}
        {session.status === "creating" && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleGenerate}
              className="btn-gold flex items-center gap-2"
            >
              <ZapIcon className="w-4 h-4" />
              Generate Design
            </button>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center gap-2 text-ink-steel text-sm mt-4">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div key={i} className="w-1.5 h-1.5 bg-gold rounded-full animate-pulse" />
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
            disabled={isLoading || session.status === "generating"}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading || session.status === "generating"}
            className="btn-gold p-3 disabled:opacity-40"
          >
            <SendHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
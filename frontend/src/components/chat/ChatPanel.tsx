"use client"
import { useRef, useEffect, useState } from "react"
import { SendHorizontalIcon, ZapIcon } from "lucide-react"
import { useStore } from "@/store/useStore"
import { classifyPrompt, getMCQTemplate, createSession } from "@/lib/api"
import ChatMessageItem from "./ChatMessage"

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
    setSessionStatus,
  } = useStore()

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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

  const handleSubmit = async () => {
    const prompt = input.trim()
    if (!prompt || isLoading) return
    setInput("")
    setIsLoading(true)

    // Start session in store — adds user message + "analysing..." message
    startSession(prompt)

    try {
      // Phase A: Classify
      const classification = await classifyPrompt(prompt)
      setClassification(classification)

      // Phase B: Fetch MCQ template (0 Gemini calls)
      const template = await getMCQTemplate(classification.type)
      setMcqTemplate(template)

    } catch (err) {
      addMessage("assistant", "text", `Something went wrong: ${(err as Error).message}. Please try again.`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  // After all MCQ answered — create session and move to generation
  const handleGenerate = async () => {
    if (!session.designType || session.status !== "creating") return
    setIsLoading(true)
    setSessionStatus("creating")

    try {
      const result = await createSession({
        prompt: session.prompt,
        design_type: session.designType,
        context: session.context,
      })
      setSessionId(result.session_id)
      addMessage("assistant", "text",
        "Session created. Generation pipeline activates in Stage 4 — for now, your design context has been saved."
      )
      setSessionStatus("complete")
    } catch (err) {
      addMessage("assistant", "text", `Failed to create session: ${(err as Error).message}`)
      setSessionStatus("error")
    } finally {
      setIsLoading(false)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-surface-black">

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto py-8 space-y-6">

        {/* Empty state — hero, full darkness, gold relief only on accent */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full px-8 text-center space-y-8">
            <div className="space-y-4 max-w-2xl">
              <h1 className="text-sub md:text-section font-normal text-ink-white uppercase">
                What System Do You Want To Design?
              </h1>
              <p className="text-body text-ink-ash max-w-md mx-auto">
                Describe a product or component and I&rsquo;ll guide you through HLD or LLD — with real-world references.
              </p>
            </div>

            {/* Example prompt ghost buttons */}
            <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
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

        {/* Generate button — Gold Accent CTA, appears after all MCQ complete */}
        {session.status === "creating" && (
          <div className="px-6">
            <button
              onClick={handleGenerate}
              disabled={isLoading}
              className="btn-accent"
            >
              <ZapIcon size={16} />
              Generate Design
            </button>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="px-6 flex items-center gap-3 text-btnsm uppercase tracking-wide text-ink-ash">
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 bg-gold animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
            <span>Processing…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar — sharp corners, charcoal surface, gold focus + send */}
      <div className="px-6 pb-6 pt-3 border-t border-[#202020]">
        <div className="relative bg-surface-charcoal rounded-none border border-white/15 focus-within:border-gold transition-colors">
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
            placeholder="Describe a system to design…"
            rows={1}
            disabled={isLoading || (session.status !== "idle" && session.status !== "error")}
            className="w-full bg-transparent resize-none px-4 py-4 pr-14
                       text-body text-ink-white placeholder:text-ink-steel
                       focus:outline-none disabled:opacity-40 max-h-40"
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className="absolute right-3 bottom-3 p-2 rounded-none
                       bg-gold text-surface-black hover:bg-gold-dark
                       disabled:opacity-30 disabled:cursor-not-allowed
                       transition-colors duration-150"
          >
            <SendHorizontalIcon size={15} />
          </button>
        </div>
        <p className="text-micro uppercase tracking-wide text-ink-steel text-center mt-3">
          Shift+Enter for new line · Enter to send
        </p>
      </div>
    </div>
  )
}
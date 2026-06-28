// frontend/src/components/chat/ChatMessage.tsx
"use client"
import { clsx } from "clsx"
import { CheckCircle2Icon, XCircleIcon, Loader2Icon, SearchIcon, RocketIcon, SparklesIcon } from "lucide-react"
import type { ChatMessage, MCQTemplate } from "@/types"
import MCQChipGroup from "@/components/mcq/MCQChipGroup"
import { useStore } from "@/store/useStore"
import { LogoAvatar } from "@/components/brand/Logo"

interface Props {
  message: ChatMessage
  mcqTemplate?: MCQTemplate
}

function SimpleMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g)
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**"))
          return <strong key={i} className="font-medium text-gold-text">{part.slice(2,-2)}</strong>
        if (part.startsWith("*") && part.endsWith("*"))
          return <em key={i} className="italic text-ink-ash">{part.slice(1,-1)}</em>
        return <span key={i}>{part}</span>
      })}
    </span>
  )
}

const NAMED_STATUS_ICONS = { search: SearchIcon, rocket: RocketIcon, sparkles: SparklesIcon } as const

function StatusLine({ message }: { message: ChatMessage }) {
  const isError = message.type === "error"
  const sectionStatus = message.metadata?.sectionStatus
  const isInProgress = sectionStatus === "started"
  const isSectionComplete = sectionStatus === "complete"
  const namedIcon = message.metadata?.icon
    ? NAMED_STATUS_ICONS[message.metadata.icon as keyof typeof NAMED_STATUS_ICONS]
    : undefined

  let Icon = namedIcon ?? CheckCircle2Icon
  if (isError) Icon = XCircleIcon
  else if (isInProgress) Icon = Loader2Icon

  const colorClass = isError ? "text-red-400"
    : isInProgress ? "text-ink-steel"
    : isSectionComplete || namedIcon ? "text-gold"
    : "text-ink-ash"

  return (
    <div className="flex items-center gap-2 text-xs py-0.5">
      <Icon className={clsx("w-3.5 h-3.5 shrink-0", colorClass, isInProgress && "animate-spin")} />
      <span className={clsx("leading-relaxed", isError ? "text-red-300" : "text-ink-ash")}>
        <SimpleMarkdown text={message.content} />
      </span>
    </div>
  )
}

export default function ChatMessageItem({ message, mcqTemplate }: Props) {
  const { answerMcqCategory, nextMcqCategory } = useStore()
  const isUser = message.role === "user"

  return (
    <div className={clsx("flex gap-2.5 px-4", isUser ? "justify-end" : "justify-start")}>

      {!isUser && <LogoAvatar size={28} className="mt-0.5 shrink-0" />}

      <div className={clsx("max-w-[88%] text-xs leading-relaxed", isUser ? "msg-user px-3 py-2.5" : "space-y-2")}>

        {message.type === "classification" && message.metadata?.classification && (
          <div className="msg-assistant space-y-2">
            <p className="text-xs leading-relaxed"><SimpleMarkdown text={message.content} /></p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-micro uppercase tracking-wide text-ink-steel">Not right?</span>
              <button
                className="btn-ghost text-btnsm py-1.5 px-2.5 text-[11px]"
                onClick={() => {
                  const correction = message.metadata?.classification?.suggested_correction
                  if (correction) useStore.getState().setDesignType(correction)
                }}
              >
                Switch to {message.metadata.classification.suggested_correction}
              </button>
            </div>
          </div>
        )}

        {message.type === "mcq" && message.metadata?.mcqCategory && mcqTemplate && (
          <div className="msg-assistant space-y-2">
            <p className="label-caps text-[10px]">{message.metadata.mcqCategory.label}</p>
            <p className="text-xs text-ink-white">{message.content}</p>
            <MCQChipGroup
              category={message.metadata.mcqCategory}
              categoryIndex={message.metadata.mcqCategoryIndex ?? 0}
              totalCategories={mcqTemplate.categories.length}
              onSubmit={(categoryId, selectedIds, freeText) => {
                answerMcqCategory(categoryId, selectedIds, freeText)
                nextMcqCategory()
              }}
            />
          </div>
        )}

        {message.type === "text" && (
          <div className={isUser ? "" : "msg-assistant"}>
            <p className="text-xs leading-relaxed whitespace-pre-wrap">
              <SimpleMarkdown text={message.content} />
            </p>
          </div>
        )}

        {(message.type === "status" || message.type === "error") && <StatusLine message={message} />}
      </div>

      {isUser && (
        <div className="w-7 h-7 bg-transparent border border-white/50 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-[11px] text-ink-white">Y</span>
        </div>
      )}
    </div>
  )
}
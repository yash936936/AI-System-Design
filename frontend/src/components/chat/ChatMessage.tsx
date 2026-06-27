"use client"
import { clsx } from "clsx"
import {
  CheckCircle2Icon,
  XCircleIcon,
  Loader2Icon,
  SearchIcon,
  RocketIcon,
  SparklesIcon,
} from "lucide-react"
import type { ChatMessage, MCQTemplate } from "@/types"
import MCQChipGroup from "@/components/mcq/MCQChipGroup"
import { useStore } from "@/store/useStore"
import { LogoAvatar } from "@/components/brand/Logo"

interface Props {
  message: ChatMessage
  mcqTemplate?: MCQTemplate
}

// Minimal markdown-like renderer — bold and italic only
function SimpleMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g)
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i} className="font-medium text-gold-text">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith("*") && part.endsWith("*")) {
          return <em key={i} className="italic text-ink-ash">{part.slice(1, -1)}</em>
        }
        return <span key={i}>{part}</span>
      })}
    </span>
  )
}

// Named-icon registry for status messages that carry a specific
// `metadata.icon` hint (search / rocket / sparkles) rather than a
// section lifecycle state.
const NAMED_STATUS_ICONS = {
  search: SearchIcon,
  rocket: RocketIcon,
  sparkles: SparklesIcon,
} as const

/**
 * Renders "status" and "error" message types — pipeline progress
 * updates (retrieval started, section generating, section complete,
 * generation failed). Previously these types had no matching render
 * branch at all, which left a blank avatar-only row in the transcript
 * for every one of them; that's the dead space between responses.
 */
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

  const colorClass = isError
    ? "text-red-400"
    : isInProgress
      ? "text-ink-steel"
      : isSectionComplete || namedIcon
        ? "text-gold"
        : "text-ink-ash"

  return (
    <div className="flex items-center gap-2.5 text-body py-0.5">
      <Icon className={clsx("w-4 h-4 shrink-0", colorClass, isInProgress && "animate-spin")} />
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
    <div className={clsx("flex gap-3 px-6", isUser ? "justify-end" : "justify-start")}>

      {/* Assistant avatar — brand mark on filled hexagon */}
      {!isUser && <LogoAvatar size={32} className="mt-0.5" />}

      {/* Message content */}
      <div className={clsx(
        "max-w-[85%] text-body leading-relaxed",
        isUser
          ? "msg-user px-4 py-3"
          : "space-y-3"
      )}>
        {/* Classification message — shows switch ghost-button */}
        {message.type === "classification" && message.metadata?.classification && (
          <div className="msg-assistant space-y-3">
            <p className="text-body leading-relaxed">
              <SimpleMarkdown text={message.content} />
            </p>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-micro uppercase tracking-wide text-ink-steel">Not right?</span>
              <button
                className="btn-ghost text-btnsm py-2 px-3"
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

        {/* MCQ message — renders chip group */}
        {message.type === "mcq" && message.metadata?.mcqCategory && mcqTemplate && (
          <div className="msg-assistant space-y-3">
            <p className="label-caps">
              {message.metadata.mcqCategory.label}
            </p>
            <p className="text-body text-ink-white">{message.content}</p>
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

        {/* Plain text message */}
        {message.type === "text" && (
          <div className={isUser ? "" : "msg-assistant"}>
            <p className="text-body leading-relaxed whitespace-pre-wrap">
              <SimpleMarkdown text={message.content} />
            </p>
          </div>
        )}

        {/* Status / error message — pipeline progress updates */}
        {(message.type === "status" || message.type === "error") && (
          <StatusLine message={message} />
        )}
      </div>

      {/* User avatar — sharp square, white border */}
      {isUser && (
        <div className="w-8 h-8 bg-transparent border border-white/50 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-btnsm text-ink-white">Y</span>
        </div>
      )}
    </div>
  )
}

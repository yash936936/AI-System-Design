"use client"
import { clsx } from "clsx"
import type { ChatMessage, MCQTemplate } from "@/types"
import MCQChipGroup from "@/components/mcq/MCQChipGroup"
import { useStore } from "@/store/useStore"

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
          return <strong key={i} className="font-semibold text-text-primary">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith("*") && part.endsWith("*")) {
          return <em key={i} className="italic text-text-secondary">{part.slice(1, -1)}</em>
        }
        return <span key={i}>{part}</span>
      })}
    </span>
  )
}

export default function ChatMessageItem({ message, mcqTemplate }: Props) {
  const { answerMcqCategory, nextMcqCategory, session } = useStore()
  const isUser = message.role === "user"

  return (
    <div className={clsx("flex gap-3 px-4", isUser ? "justify-end" : "justify-start")}>

      {/* Assistant avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-accent-primary flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-xs font-bold text-white">S</span>
        </div>
      )}

      {/* Message content */}
      <div className={clsx(
        "max-w-[85%] text-sm leading-relaxed",
        isUser
          ? "bg-bg-input border border-border rounded-2xl rounded-tr-sm px-4 py-2.5 text-text-primary"
          : "space-y-2"
      )}>
        {/* Classification message — shows switch chip */}
        {message.type === "classification" && message.metadata?.classification && (
          <div className="msg-assistant space-y-2">
            <p className="text-sm leading-relaxed">
              <SimpleMarkdown text={message.content} />
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-text-muted">Not right?</span>
              <button
                className="chip text-xs"
                onClick={() => {
                  const correction = message.metadata!.classification!.suggested_correction
                  useStore.getState().setDesignType(correction)
                }}
              >
                Switch to {message.metadata.classification.suggested_correction}
              </button>
            </div>
          </div>
        )}

        {/* MCQ message — renders chip group */}
        {message.type === "mcq" && message.metadata?.mcqCategory && mcqTemplate && (
          <div className="msg-assistant space-y-2">
            <p className="text-sm font-medium text-text-secondary">
              {message.metadata.mcqCategory.label}
            </p>
            <p className="text-sm text-text-primary">{message.content}</p>
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
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              <SimpleMarkdown text={message.content} />
            </p>
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-bg-input border border-border flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-xs text-text-secondary">Y</span>
        </div>
      )}
    </div>
  )
}

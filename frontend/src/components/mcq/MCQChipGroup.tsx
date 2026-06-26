"use client"
import { useState } from "react"
import { CheckIcon, PlusIcon } from "lucide-react"
import { clsx } from "clsx"
import type { MCQCategory } from "@/types"

interface MCQChipGroupProps {
  category: MCQCategory
  categoryIndex: number
  totalCategories: number
  onSubmit: (categoryId: string, selectedIds: string[], freeText?: string) => void
}

export default function MCQChipGroup({
  category,
  categoryIndex,
  totalCategories,
  onSubmit,
}: MCQChipGroupProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [freeText, setFreeText] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const toggle = (id: string) => {
    if (submitted) return
    setSelected((prev) => {
      const next = new Set(prev)
      if (category.type === "single_select") {
        next.clear()
        next.add(id)
      } else {
        if (next.has(id)) next.delete(id)
        else next.add(id)
      }
      return next
    })
  }

  const handleSubmit = () => {
    if (selected.size === 0 && !freeText.trim()) return
    setSubmitted(true)
    onSubmit(category.id, Array.from(selected), freeText.trim() || undefined)
  }

  return (
    <div className="mt-2 space-y-3">
      {/* Progress indicator */}
      <p className="text-xs text-text-muted">
        Step {categoryIndex + 1} of {totalCategories}
      </p>

      {/* Chip grid */}
      <div className="flex flex-wrap gap-2">
        {category.options.map((opt) => {
          const isSelected = selected.has(opt.id)
          return (
            <button
              key={opt.id}
              onClick={() => toggle(opt.id)}
              disabled={submitted}
              className={clsx(
                "chip",
                isSelected && "selected",
                submitted && "opacity-60 cursor-default"
              )}
            >
              {isSelected && <CheckIcon size={12} className="mr-1" />}
              {opt.label}
            </button>
          )
        })}
      </div>

      {/* Free text field */}
      {category.allow_free_text && (
        <div className="flex items-center gap-2">
          <PlusIcon size={14} className="text-text-muted shrink-0" />
          <input
            type="text"
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            disabled={submitted}
            placeholder={category.free_text_placeholder}
            className="flex-1 bg-bg-input border border-border rounded-lg px-3 py-1.5
                       text-sm text-text-primary placeholder:text-text-muted
                       focus:outline-none focus:border-accent-primary
                       disabled:opacity-60"
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>
      )}

      {/* Submit button */}
      {!submitted && (
        <button
          onClick={handleSubmit}
          disabled={selected.size === 0 && !freeText.trim()}
          className="px-4 py-1.5 rounded-lg text-sm font-medium
                     bg-accent-primary text-white hover:bg-accent-hover
                     disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors duration-150"
        >
          {categoryIndex + 1 < totalCategories ? "Next →" : "Review Answers"}
        </button>
      )}

      {/* Submitted confirmation */}
      {submitted && (
        <p className="text-xs text-text-muted flex items-center gap-1">
          <CheckIcon size={12} className="text-accent-primary" />
          {Array.from(selected).map(id =>
            category.options.find(o => o.id === id)?.label
          ).filter(Boolean).join(", ")}
          {freeText && ` + "${freeText}"`}
        </p>
      )}
    </div>
  )
}

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
    <div className="mt-2 space-y-4">
      {/* Progress indicator */}
      <p className="text-micro uppercase tracking-wide text-ink-steel">
        Step {categoryIndex + 1} of {totalCategories}
      </p>

      {/* Option grid — ghost buttons, gold when selected */}
      <div className="flex flex-wrap gap-2.5">
        {category.options.map((opt) => {
          const isSelected = selected.has(opt.id)
          return (
            <button
              key={opt.id}
              onClick={() => toggle(opt.id)}
              disabled={submitted}
              className={clsx(
                "btn-ghost text-btnsm py-2.5 px-4 opacity-100",
                isSelected && "selected",
                submitted && !isSelected && "opacity-40 cursor-default",
                submitted && "cursor-default"
              )}
            >
              {isSelected && <CheckIcon size={13} strokeWidth={2.5} />}
              {opt.label}
            </button>
          )
        })}
      </div>

      {/* Free text field */}
      {category.allow_free_text && (
        <div className="flex items-center gap-2.5">
          <PlusIcon size={14} className="text-ink-steel shrink-0" />
          <input
            type="text"
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            disabled={submitted}
            placeholder={category.free_text_placeholder}
            className="input-dark flex-1 py-2.5 text-btnsm disabled:opacity-60"
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>
      )}

      {/* Submit button — Gold Accent CTA */}
      {!submitted && (
        <button
          onClick={handleSubmit}
          disabled={selected.size === 0 && !freeText.trim()}
          className="btn-accent py-2.5 px-5 text-btnsm"
        >
          {categoryIndex + 1 < totalCategories ? "Next →" : "Review Answers"}
        </button>
      )}

      {/* Submitted confirmation */}
      {submitted && (
        <p className="text-micro uppercase tracking-wide text-ink-steel flex items-center gap-1.5">
          <CheckIcon size={12} className="text-gold" />
          {Array.from(selected).map(id =>
            category.options.find(o => o.id === id)?.label
          ).filter(Boolean).join(", ")}
          {freeText && ` + "${freeText}"`}
        </p>
      )}
    </div>
  )
}
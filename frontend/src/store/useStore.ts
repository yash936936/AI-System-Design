import { create } from "zustand"
import { immer } from "zustand/middleware/immer"
import type {
  Session, SessionContext, SessionStatus, DesignType,
  ChatMessage, MessageType, MessageRole,
  ArtifactState, ArtifactTab,
  ClassifyResponse, MCQTemplate, MCQCategory,
} from "@/types"

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeId() {
  return Math.random().toString(36).slice(2, 10)
}

function makeMessage(
  role: MessageRole,
  type: MessageType,
  content: string,
  metadata?: ChatMessage["metadata"],
): ChatMessage {
  return { id: makeId(), role, type, content, metadata, createdAt: Date.now() }
}

const EMPTY_SESSION: Session = {
  prompt: "",
  mcqAnswers: {},
  mcqFreeText: {},
  context: {
    functional_reqs: [],
    out_of_scope: [],
    user_actors: [],
    bottleneck_focus: [],
  },
  status: "idle",
  currentMcqIndex: 0,
}

// ── Store interface ───────────────────────────────────────────────────────────

interface Store {
  // Chat history (sidebar)
  sessionHistory: Array<{ id: string; title: string; date: string }>

  // Active session
  session: Session
  messages: ChatMessage[]
  artifact: ArtifactState

  // Actions — session flow
  startSession: (prompt: string) => void
  setClassification: (result: ClassifyResponse) => void
  setDesignType: (type: DesignType) => void
  setMcqTemplate: (template: MCQTemplate) => void
  answerMcqCategory: (categoryId: string, selectedIds: string[], freeText?: string) => void
  nextMcqCategory: () => void
  setSessionStatus: (status: SessionStatus) => void
  setSessionId: (id: string) => void
  resetSession: () => void

  // Actions — messages
  addMessage: (role: MessageRole, type: MessageType, content: string, metadata?: ChatMessage["metadata"]) => void

  // Actions — artifact
  setArtifactVisible: (visible: boolean) => void
  setArtifactTab: (tab: ArtifactTab) => void
  setArtifactSection: (section: string, data: Record<string, unknown>) => void
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useStore = create<Store>()(
  immer((set) => ({
    sessionHistory: [],
    session: { ...EMPTY_SESSION },
    messages: [],
    artifact: {
      activeTab: "diagram",
      isVisible: false,
    },

    // ── Session flow ──────────────────────────────────────────────────────────

    startSession: (prompt) =>
      set((state) => {
        state.session = { ...EMPTY_SESSION, prompt, status: "classifying" }
        state.messages = [
          makeMessage("user", "text", prompt),
          makeMessage("assistant", "text", "Analysing your prompt to determine design type…"),
        ]
        state.artifact.isVisible = false
      }),

    setClassification: (result) =>
      set((state) => {
        state.session.classification = result
        state.session.designType = result.type
        state.session.status = "mcq"
        // Replace the last assistant message with the classification result
        const last = state.messages[state.messages.length - 1]
        if (last?.role === "assistant") {
          last.type = "classification"
          last.content = result.type === "HLD"
            ? `This looks like a **High-Level Design** question — I'll walk you through the full HLD process: architecture, capacity, data model, API design, and trade-offs.\n\n*Confidence: ${Math.round(result.confidence * 100)}% — ${result.reasoning}*`
            : `This is a **Low-Level Design** question — I'll focus on the component internals: data structures, concurrency model, algorithms, and API contracts.\n\n*Confidence: ${Math.round(result.confidence * 100)}% — ${result.reasoning}*`
          last.metadata = { classification: result }
        }
      }),

    setDesignType: (type) =>
      set((state) => {
        state.session.designType = type
        if (state.session.classification) {
          state.session.classification.type = type
        }
      }),

    setMcqTemplate: (template) =>
      set((state) => {
        state.session.mcqTemplate = template
        state.session.currentMcqIndex = 0
        // Push first MCQ category as assistant message
        const firstCat = template.categories[0]
        if (firstCat) {
          state.messages.push(
            makeMessage("assistant", "mcq",
              `Let's gather some requirements. ${firstCat.question}`,
              { mcqCategory: firstCat, mcqCategoryIndex: 0 }
            )
          )
        }
      }),

    answerMcqCategory: (categoryId, selectedIds, freeText) =>
      set((state) => {
        state.session.mcqAnswers[categoryId] = selectedIds
        if (freeText) state.session.mcqFreeText[categoryId] = freeText
      }),

    nextMcqCategory: () =>
      set((state) => {
        const template = state.session.mcqTemplate
        if (!template) return
        const nextIndex = state.session.currentMcqIndex + 1
        state.session.currentMcqIndex = nextIndex
        const nextCat = template.categories[nextIndex]
        if (nextCat) {
          state.messages.push(
            makeMessage("assistant", "mcq",
              nextCat.question,
              { mcqCategory: nextCat, mcqCategoryIndex: nextIndex }
            )
          )
        } else {
          // All categories answered — push summary
          state.session.status = "creating"
          state.messages.push(
            makeMessage("assistant", "text",
              "All requirements captured. Review your answers below and click **Generate Design** when ready."
            )
          )
        }
      }),

    setSessionStatus: (status) =>
      set((state) => { state.session.status = status }),

    setSessionId: (id) =>
      set((state) => { state.session.id = id }),

    resetSession: () =>
      set((state) => {
        state.session = { ...EMPTY_SESSION }
        state.messages = []
        state.artifact = { activeTab: "diagram", isVisible: false }
      }),

    // ── Messages ──────────────────────────────────────────────────────────────

    addMessage: (role, type, content, metadata) =>
      set((state) => {
        state.messages.push(makeMessage(role, type, content, metadata))
      }),

    // ── Artifact ──────────────────────────────────────────────────────────────

    setArtifactVisible: (visible) =>
      set((state) => { state.artifact.isVisible = visible }),

    setArtifactTab: (tab) =>
      set((state) => { state.artifact.activeTab = tab }),

    setArtifactSection: (section, data) =>
      set((state) => {
        (state.artifact as Record<string, unknown>)[section] = data
        state.artifact.isVisible = true
        state.artifact.activeTab = section as ArtifactTab
      }),
  }))
)

/**
 * SysDesign AI — Zustand Store
 * =============================
 * 
 * Central state management for the application.
 * Handles session flow, messages, artifact panel, and SSE streaming.
 * 
 * @version 3.0.0
 */

import { create } from "zustand"
import { immer } from "zustand/middleware/immer"
import type {
  // Core domain
  Session,
  SessionContext,
  SessionStatus,
  DesignType,
  SessionHistoryItem,
  
  // Chat & messages
  ChatMessage,
  MessageType,
  MessageRole,
  ChatMessageMetadata,
  
  // Artifact
  ArtifactState,
  ArtifactTab,
  
  // Phase A
  ClassifyResponse,
  
  // Phase B
  MCQTemplate,
  MCQCategory,
  
  // Phase D
  SSEEvent,
  SectionId,
  SectionPayload,
  
  // Section data types
  ArchitectureData,
  CapacityData,
  DataModelData,
  ApiDesignData,
  StackData,
} from "@/types"

// Import constants for type-safe references
import {
  SESSION_STATUS,
  ARTIFACT_TABS,
  SECTION_NAMES,
  STORAGE_KEYS,
} from "@/types"

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generate a unique ID for messages and entities.
 */
function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

/**
 * Create a new chat message with all required fields.
 */
function makeMessage(
  role: MessageRole,
  type: MessageType,
  content: string,
  metadata?: ChatMessageMetadata,
): ChatMessage {
  return {
    id: makeId(),
    role,
    type,
    content,
    metadata,
    createdAt: Date.now(),
  }
}

/**
 * Empty session template.
 */
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
  status: SESSION_STATUS.IDLE,
  currentMcqIndex: 0,
}

/**
 * Map section IDs to artifact tab IDs.
 */
const SECTION_TO_TAB: Record<SectionId, ArtifactTab> = {
  architecture: ARTIFACT_TABS.DIAGRAM,
  capacity: ARTIFACT_TABS.CAPACITY,
  data_model: ARTIFACT_TABS.DATA_MODEL,
  api_design: ARTIFACT_TABS.API,
  stack: ARTIFACT_TABS.STACK,
}

// ═══════════════════════════════════════════════════════════════════════════════
// STORE INTERFACE
// ═══════════════════════════════════════════════════════════════════════════════

interface Store {
  // ── State ───────────────────────────────────────────────────────────────
  
  /** Session history for sidebar */
  sessionHistory: SessionHistoryItem[]
  
  /** Active session */
  session: Session
  
  /** Chat messages */
  messages: ChatMessage[]
  
  /** Artifact panel state */
  artifact: ArtifactState
  
  // ── Session Flow Actions ────────────────────────────────────────────────
  
  /** Start a new session with user prompt */
  startSession: (prompt: string) => void
  
  /** Set classification result from Phase A */
  setClassification: (result: ClassifyResponse) => void
  
  /** Override design type */
  setDesignType: (type: DesignType) => void
  
  /** Set MCQ template from Phase B */
  setMcqTemplate: (template: MCQTemplate) => void
  
  /** Record user's answer to an MCQ category */
  answerMcqCategory: (categoryId: string, selectedIds: string[], freeText?: string) => void
  
  /** Move to next MCQ category */
  nextMcqCategory: () => void
  
  /** Update session status */
  setSessionStatus: (status: SessionStatus) => void
  
  /** Set session ID after creation */
  setSessionId: (id: string) => void
  
  /** Reset session to initial state */
  resetSession: () => void
  
  /** Add session to history */
  addToHistory: (item: SessionHistoryItem) => void
  
  /** Remove session from history */
  removeFromHistory: (id: string) => void
  
  // ── Message Actions ─────────────────────────────────────────────────────
  
  /** Add a new message */
  addMessage: (
    role: MessageRole,
    type: MessageType,
    content: string,
    metadata?: ChatMessageMetadata,
  ) => void
  
  /** Update an existing message */
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  
  /** Delete a message */
  deleteMessage: (id: string) => void
  
  // ── Artifact Actions ────────────────────────────────────────────────────
  
  /** Show/hide artifact panel */
  setArtifactVisible: (visible: boolean) => void
  
  /** Switch artifact tab */
  setArtifactTab: (tab: ArtifactTab) => void
  
  /** Set section data in artifact */
  setArtifactSection: (section: SectionId, data: SectionPayload) => void
  
  /** Set loading state for a section */
  setArtifactLoading: (section: ArtifactTab, loading: boolean) => void
  
  /** Set error state for a section */
  setArtifactError: (section: ArtifactTab, error: string | null) => void
  
  // ── Phase D: SSE Streaming Actions ──────────────────────────────────────
  
  /** Handle incoming SSE event */
  handleSSEEvent: (event: SSEEvent) => void
  
  /** Handle stream completion */
  handleStreamDone: () => void
  
  /** Handle stream error */
  handleStreamError: (error: string, errorCode?: string) => void
}

// ═══════════════════════════════════════════════════════════════════════════════
// STORE IMPLEMENTATION
// ═══════════════════════════════════════════════════════════════════════════════

export const useStore = create<Store>()(
  immer((set, get) => ({
    // ── Initial State ─────────────────────────────────────────────────────
    
    sessionHistory: [],
    session: { ...EMPTY_SESSION },
    messages: [],
    artifact: {
      activeTab: ARTIFACT_TABS.DIAGRAM,
      isVisible: false,
      loading: {},
      errors: {},
    },

    // ═══════════════════════════════════════════════════════════════════════
    // SESSION FLOW ACTIONS
    // ═══════════════════════════════════════════════════════════════════════

    startSession: (prompt) =>
      set((state) => {
        state.session = {
          ...EMPTY_SESSION,
          prompt,
          status: SESSION_STATUS.CLASSIFYING,
          createdAt: Date.now(),
        }
        state.messages = [
          makeMessage("user", "text", prompt),
          makeMessage(
            "assistant",
            "text",
            "Analysing your prompt to determine design type…",
          ),
        ]
        state.artifact = {
          activeTab: ARTIFACT_TABS.DIAGRAM,
          isVisible: false,
          loading: {},
          errors: {},
        }
      }),

    setClassification: (result) =>
      set((state) => {
        state.session.classification = result
        state.session.designType = result.type
        state.session.status = SESSION_STATUS.MCQ

        // Update the last assistant message
        const last = state.messages[state.messages.length - 1]
        if (last?.role === "assistant") {
          last.type = "classification"
          last.content =
            result.type === "HLD"
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

        const firstCat = template.categories[0]
        if (firstCat) {
          state.messages.push(
            makeMessage(
              "assistant",
              "mcq",
              `Let's gather some requirements. ${firstCat.question}`,
              { mcqCategory: firstCat, mcqCategoryIndex: 0 },
            ),
          )
        }
      }),

    answerMcqCategory: (categoryId, selectedIds, freeText) =>
      set((state) => {
        state.session.mcqAnswers[categoryId] = selectedIds
        if (freeText) {
          state.session.mcqFreeText[categoryId] = freeText
        }
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
            makeMessage("assistant", "mcq", nextCat.question, {
              mcqCategory: nextCat,
              mcqCategoryIndex: nextIndex,
            }),
          )
        } else {
          // All MCQs complete
          state.session.status = SESSION_STATUS.CREATING
          state.messages.push(
            makeMessage(
              "assistant",
              "text",
              "All requirements captured. Review your answers below and click **Generate Design** when ready.",
            ),
          )
        }
      }),

    setSessionStatus: (status) =>
      set((state) => {
        state.session.status = status
      }),

    setSessionId: (id) =>
      set((state) => {
        state.session.id = id
      }),

    resetSession: () =>
      set((state) => {
        state.session = { ...EMPTY_SESSION }
        state.messages = []
        state.artifact = {
          activeTab: ARTIFACT_TABS.DIAGRAM,
          isVisible: false,
          loading: {},
          errors: {},
        }
      }),

    addToHistory: (item) =>
      set((state) => {
        // Add to beginning of history
        state.sessionHistory.unshift(item)
        // Keep only last 50 sessions
        if (state.sessionHistory.length > 50) {
          state.sessionHistory = state.sessionHistory.slice(0, 50)
        }
        // Persist to localStorage
        try {
          localStorage.setItem(
            STORAGE_KEYS.SESSION_HISTORY,
            JSON.stringify(state.sessionHistory),
          )
        } catch (err) {
          console.error("Failed to save session history:", err)
        }
      }),

    removeFromHistory: (id) =>
      set((state) => {
        state.sessionHistory = state.sessionHistory.filter((s) => s.id !== id)
        try {
          localStorage.setItem(
            STORAGE_KEYS.SESSION_HISTORY,
            JSON.stringify(state.sessionHistory),
          )
        } catch (err) {
          console.error("Failed to save session history:", err)
        }
      }),

    // ═══════════════════════════════════════════════════════════════════════
    // MESSAGE ACTIONS
    // ═══════════════════════════════════════════════════════════════════════

    addMessage: (role, type, content, metadata) =>
      set((state) => {
        state.messages.push(makeMessage(role, type, content, metadata))
      }),

    updateMessage: (id, updates) =>
      set((state) => {
        const msg = state.messages.find((m) => m.id === id)
        if (msg) {
          Object.assign(msg, updates)
        }
      }),

    deleteMessage: (id) =>
      set((state) => {
        state.messages = state.messages.filter((m) => m.id !== id)
      }),

    // ═══════════════════════════════════════════════════════════════════════
    // ARTIFACT ACTIONS
    // ═══════════════════════════════════════════════════════════════════════

    setArtifactVisible: (visible) =>
      set((state) => {
        state.artifact.isVisible = visible
      }),

    setArtifactTab: (tab) =>
      set((state) => {
        state.artifact.activeTab = tab
      }),

    setArtifactSection: (section, data) =>
      set((state) => {
        const tab = SECTION_TO_TAB[section]
        if (!tab) {
          console.warn(`Unknown section: ${section}`)
          return
        }

        // Type-safe assignment based on section
        switch (section) {
          case "architecture":
            state.artifact.diagram = data as ArchitectureData
            break
          case "capacity":
            state.artifact.capacity = data as CapacityData
            break
          case "data_model":
            state.artifact.data_model = data as DataModelData
            break
          case "api_design":
            state.artifact.api = data as ApiDesignData
            break
          case "stack":
            state.artifact.stack = data as StackData
            break
        }

        state.artifact.isVisible = true
        state.artifact.activeTab = tab

        // Clear loading and error states
        if (state.artifact.loading) {
          state.artifact.loading[tab] = false
        }
        if (state.artifact.errors) {
          state.artifact.errors[tab] = undefined
        }
      }),

    setArtifactLoading: (section, loading) =>
      set((state) => {
        if (!state.artifact.loading) {
          state.artifact.loading = {}
        }
        state.artifact.loading[section] = loading
      }),

    setArtifactError: (section, error) =>
      set((state) => {
        if (!state.artifact.errors) {
          state.artifact.errors = {}
        }
        if (error) {
          state.artifact.errors[section] = error
        } else {
          delete state.artifact.errors[section]
        }
      }),

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE D: SSE STREAMING ACTIONS
    // ═══════════════════════════════════════════════════════════════════════

    handleSSEEvent: (event: SSEEvent) =>
      set((state) => {
        // Handle discriminated union with type narrowing
        switch (event.type) {
          case "ping":
            // Connection established - no action needed
            console.debug("SSE connection established:", event.session_id)
            break

          case "heartbeat":
            // Keep-alive ping - no action needed
            break

          case "section.start":
            // Section generation started
            state.session.status = SESSION_STATUS.GENERATING
            state.messages.push(
              makeMessage(
                "assistant",
                "status",
                `🔄 Generating **${SECTION_NAMES[event.section]}**…`,
                {
                  section: event.section,
                  sectionStatus: "started",
                  startedAt: event.timestamp,
                },
              ),
            )
            // Set loading state
            const startTab = SECTION_TO_TAB[event.section]
            if (startTab) {
              if (!state.artifact.loading) state.artifact.loading = {}
              state.artifact.loading[startTab] = true
            }
            break

          case "section.done":
            // Section generation complete
            const doneTab = SECTION_TO_TAB[event.section]
            if (doneTab && event.payload) {
              // Type-safe assignment
              switch (event.section) {
                case "architecture":
                  state.artifact.diagram = event.payload as ArchitectureData
                  break
                case "capacity":
                  state.artifact.capacity = event.payload as CapacityData
                  break
                case "data_model":
                  state.artifact.data_model = event.payload as DataModelData
                  break
                case "api_design":
                  state.artifact.api = event.payload as ApiDesignData
                  break
                case "stack":
                  state.artifact.stack = event.payload as StackData
                  break
              }

              state.artifact.isVisible = true
              state.artifact.activeTab = doneTab

              // Clear loading state
              if (state.artifact.loading) {
                state.artifact.loading[doneTab] = false
              }
            }

            // Update the status message
            const lastMsg = state.messages[state.messages.length - 1]
            if (lastMsg?.metadata?.section === event.section) {
              lastMsg.type = "text"
              lastMsg.content = `✅ **${SECTION_NAMES[event.section]}** complete — ${event.tokens_used} tokens, ${event.duration_ms}ms${event.cached ? " (cached)" : ""}`
              lastMsg.metadata = {
                section: event.section,
                sectionStatus: "complete",
                completedAt: event.timestamp,
              }
            }
            break

          case "section.error":
            // Section generation failed
            const errorTab = SECTION_TO_TAB[event.section]
            if (errorTab) {
              if (!state.artifact.errors) state.artifact.errors = {}
              state.artifact.errors[errorTab] = event.error
              if (state.artifact.loading) {
                state.artifact.loading[errorTab] = false
              }
            }

            state.messages.push(
              makeMessage(
                "assistant",
                "error",
                `❌ Error generating ${SECTION_NAMES[event.section]}: ${event.error}`,
                {
                  section: event.section,
                  sectionStatus: "error",
                },
              ),
            )
            break

          case "pipeline.done":
            // All sections complete - handled by handleStreamDone
            break

          case "pipeline.error":
            // Fatal pipeline error - handled by handleStreamError
            break
        }
      }),

    handleStreamDone: () =>
      set((state) => {
        state.session.status = SESSION_STATUS.COMPLETE
        state.session.completedAt = Date.now()
        state.messages.push(
          makeMessage(
            "assistant",
            "text",
            "🎉 **Design generation complete!** All sections are now available in the artifact panel. You can switch between tabs to explore the architecture, capacity estimates, data model, API design, and tech stack recommendations.",
          ),
        )

        // Add to history
        const historyItem: SessionHistoryItem = {
          id: state.session.id || makeId(),
          title: state.session.prompt.slice(0, 50),
          date: new Date().toISOString(),
          designType: state.session.designType,
          status: SESSION_STATUS.COMPLETE,
        }
        state.sessionHistory.unshift(historyItem)
      }),

    handleStreamError: (error: string, errorCode?: string) =>
      set((state) => {
        state.session.status = SESSION_STATUS.ERROR
        state.session.errorMessage = error
        state.session.completedAt = Date.now()
        state.messages.push(
          makeMessage(
            "assistant",
            "error",
            `❌ Generation failed: ${error}${errorCode ? ` (Code: ${errorCode})` : ""}`,
          ),
        )
      }),
  })),
)

// ═══════════════════════════════════════════════════════════════════════════════
// PERSISTENCE & HYDRATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Load session history from localStorage on app startup.
 */
export function hydrateSessionHistory(): void {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.SESSION_HISTORY)
    if (stored) {
      const history: SessionHistoryItem[] = JSON.parse(stored)
      useStore.setState((state) => {
        state.sessionHistory = history
      })
    }
  } catch (err) {
    console.error("Failed to hydrate session history:", err)
  }
}

/**
 * Clear all stored data.
 */
export function clearAllData(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.SESSION_HISTORY)
    localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES)
    localStorage.removeItem(STORAGE_KEYS.THEME)
    useStore.getState().resetSession()
  } catch (err) {
    console.error("Failed to clear data:", err)
  }
}
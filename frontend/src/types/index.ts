// ── Design type ──────────────────────────────────────────────────────────────
export type DesignType = "HLD" | "LLD"

// ── Classify ─────────────────────────────────────────────────────────────────
export interface ClassifyResponse {
  type: DesignType
  confidence: number
  reasoning: string
  suggested_correction: DesignType
}

// ── MCQ ──────────────────────────────────────────────────────────────────────
export interface MCQOption {
  id: string
  label: string
}

export interface MCQCategory {
  id: string
  label: string
  question: string
  type: "single_select" | "multi_select"
  options: MCQOption[]
  allow_free_text: boolean
  free_text_placeholder: string
}

export interface MCQTemplate {
  design_type: string
  categories: MCQCategory[]
}

// ── Session Context (MCQ answers) ─────────────────────────────────────────────
export interface SessionContext {
  system_name?: string
  functional_reqs: string[]
  out_of_scope: string[]
  user_actors: string[]
  read_write_ratio?: string
  scale?: string
  dau?: string
  availability?: string
  consistency?: string
  latency_target?: string
  request_size_category?: string
  data_model_preference?: string
  api_style?: string
  architecture_approach?: string
  bottleneck_focus: string[]
  scalability_priority?: string
  trade_off_priority?: string
}

// ── Session ───────────────────────────────────────────────────────────────────
export type SessionStatus =
  | "idle"
  | "classifying"
  | "mcq"
  | "creating"
  | "retrieving"
  | "generating"
  | "complete"
  | "error"

export interface Session {
  id?: string
  prompt: string
  designType?: DesignType
  classification?: ClassifyResponse
  mcqTemplate?: MCQTemplate
  mcqAnswers: Record<string, string[]>   // categoryId → selected option ids
  mcqFreeText: Record<string, string>    // categoryId → free text input
  context: SessionContext
  status: SessionStatus
  currentMcqIndex: number
}

// ── Chat Message ──────────────────────────────────────────────────────────────
export type MessageRole = "user" | "assistant"
export type MessageType = "text" | "classification" | "mcq" | "sources" | "summary"

export interface ChatMessage {
  id: string
  role: MessageRole
  type: MessageType
  content: string
  metadata?: {
    classification?: ClassifyResponse
    mcqCategory?: MCQCategory
    mcqCategoryIndex?: number
  }
  createdAt: number
}

// ── Artifact ─────────────────────────────────────────────────────────────────
export type ArtifactTab = "diagram" | "capacity" | "data_model" | "api" | "stack" | "sources"

export interface ArchComponent {
  id: string
  name: string
  type: "frontend" | "backend" | "database" | "queue" | "cache" | "cdn" | "auth" | "storage" | "third_party" | "ai"
  description: string
  responsibilities: string[]
  connections: string[]
}

export interface ArtifactState {
  activeTab: ArtifactTab
  isVisible: boolean
  diagram?: { components: ArchComponent[] }
  capacity?: Record<string, unknown>
  data_model?: Record<string, unknown>
  api_design?: Record<string, unknown>
  stack?: Record<string, unknown>
  sources?: Array<{ id: string; source: string; section: string; text: string; score: number }>
}

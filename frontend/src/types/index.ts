/**
 * SysDesign AI — Type Definitions
 * ================================
 * 
 * Central type definitions for the entire application.
 * Organized by feature/phase for maintainability.
 * 
 * Sections:
 *   1. Utility Types
 *   2. Core Domain Types
 *   3. Phase A — Classification
 *   4. Phase B — MCQ (Multiple Choice Questions)
 *   5. Phase C — Retrieval
 *   6. Phase D — Generation & SSE
 *   7. Artifact Types
 *   8. Chat & Message Types
 *   9. API Types
 *   10. Component Prop Types
 *   11. Store Types
 *   12. Constants
 * 
 * @version 3.0.0
 * @author SysDesign AI
 */

// ═══════════════════════════════════════════════════════════════════════════════
// 1. UTILITY TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Makes specific keys of T optional.
 * @example
 * type User = { id: string; name: string; email?: string }
 * type PartialUser = Optional<User, 'email'> // { id: string; name: string; email?: string }
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * Makes all properties of T nullable.
 */
export type Nullable<T> = { [P in keyof T]: T[P] | null }

/**
 * Extracts the type of array elements.
 * @example
 * type User = { id: string }
 * type Users = User[]
 * type SingleUser = ArrayElement<Users> // User
 */
export type ArrayElement<T> = T extends readonly (infer U)[] ? U : never

/**
 * Makes specific keys required.
 */
export type RequiredKeys<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

/**
 * Brand type for nominal typing (prevents accidental mixing of similar types).
 * @example
 * type UserId = Brand<string, 'UserId'>
 * type SessionId = Brand<string, 'SessionId'>
 * // UserId and SessionId are not interchangeable even though both are strings
 */
export type Brand<T, B extends string> = T & { readonly __brand: B }

/**
 * Deep partial - makes all nested properties optional.
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * Extracts promise return type.
 */
export type Awaited<T> = T extends Promise<infer U> ? U : T

/**
 * Type guard helper - narrows type based on predicate.
 */
export type TypeGuard<T, U extends T> = (value: T) => value is U


// ═══════════════════════════════════════════════════════════════════════════════
// 2. CORE DOMAIN TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Design type discriminator.
 * - HLD: High-Level Design (architecture, capacity, trade-offs)
 * - LLD: Low-Level Design (data structures, algorithms, concurrency)
 */
export type DesignType = 'HLD' | 'LLD'

/**
 * Session lifecycle states.
 * 
 * State machine:
 *   idle → classifying → mcq → creating → retrieving → generating → complete
 *                                                              ↓
 *                                                           error
 */
export type SessionStatus =
  | 'idle'           // Initial state, no session
  | 'classifying'    // Phase A: Determining design type
  | 'mcq'            // Phase B: Gathering requirements via MCQ
  | 'creating'       // Creating session in backend
  | 'retrieving'     // Phase C: Fetching reference designs
  | 'generating'     // Phase D: Streaming generation
  | 'complete'       // All sections generated successfully
  | 'error'          // Fatal error occurred

/**
 * User context gathered from MCQ answers.
 * Represents the requirements for the system design.
 */
export interface SessionContext {
  /** Name of the system being designed */
  system_name?: string
  
  /** Functional requirements */
  functional_reqs: string[]
  
  /** Out of scope items */
  out_of_scope: string[]
  
  /** User actors/roles */
  user_actors: string[]
  
  /** Expected read:write ratio (e.g., "100:1") */
  read_write_ratio?: string
  
  /** Expected scale (e.g., "global", "regional") */
  scale?: string
  
  /** Daily active users */
  dau?: string
  
  /** Availability target (e.g., "99.99%") */
  availability?: string
  
  /** Consistency model (e.g., "eventual", "strong") */
  consistency?: string
  
  /** Latency target in ms */
  latency_target?: string
  
  /** Request size category */
  request_size_category?: string
  
  /** Data model preference */
  data_model_preference?: string
  
  /** API style preference */
  api_style?: string
  
  /** Architecture approach */
  architecture_approach?: string
  
  /** Known bottlenecks to focus on */
  bottleneck_focus: string[]
  
  /** Scalability priority */
  scalability_priority?: string
  
  /** Trade-off priorities */
  trade_off_priority?: string
  
  /** Additional custom requirements */
  custom_requirements?: Record<string, string>
}

/**
 * Complete session state.
 */
export interface Session {
  /** Unique session identifier */
  id?: string
  
  /** Original user prompt */
  prompt: string
  
  /** Determined design type */
  designType?: DesignType
  
  /** Classification result from Phase A */
  classification?: ClassifyResponse
  
  /** MCQ template from Phase B */
  mcqTemplate?: MCQTemplate
  
  /** User's MCQ answers (category_id → selected option_ids) */
  mcqAnswers: Record<string, string[]>
  
  /** User's free-text additions to MCQ categories */
  mcqFreeText: Record<string, string>
  
  /** Compiled context from all answers */
  context: SessionContext
  
  /** Current session status */
  status: SessionStatus
  
  /** Current MCQ category index (for multi-step flow) */
  currentMcqIndex: number
  
  /** Session creation timestamp */
  createdAt?: number
  
  /** Session completion timestamp */
  completedAt?: number
  
  /** Error message if status is 'error' */
  errorMessage?: string
}

/**
 * Sidebar session history item.
 */
export interface SessionHistoryItem {
  id: string
  title: string
  date: string
  designType?: DesignType
  status?: SessionStatus
}


// ═══════════════════════════════════════════════════════════════════════════════
// 3. PHASE A — CLASSIFICATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Classification result from Phase A.
 * Determines whether the prompt is HLD or LLD.
 */
export interface ClassifyResponse {
  /** Determined design type */
  type: DesignType
  
  /** Confidence score (0.0 to 1.0) */
  confidence: number
  
  /** Reasoning for the classification */
  reasoning: string
  
  /** Suggested correction if user disagrees */
  suggested_correction?: DesignType
  
  /** Keywords that influenced the decision */
  keywords?: string[]
}

/**
 * Classification request payload.
 */
export interface ClassifyRequest {
  prompt: string
}


// ═══════════════════════════════════════════════════════════════════════════════
// 4. PHASE B — MCQ (MULTIPLE CHOICE QUESTIONS)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Single MCQ option.
 */
export interface MCQOption {
  /** Unique option identifier */
  id: string
  
  /** Display label */
  label: string
  
  /** Optional description/help text */
  description?: string
  
  /** Whether this option is recommended */
  recommended?: boolean
  
  /** Optional icon/emoji */
  icon?: string
}

/**
 * MCQ question category.
 */
export interface MCQCategory {
  /** Unique category identifier */
  id: string
  
  /** Display label */
  label: string
  
  /** Question text */
  question: string
  
  /** Selection type */
  type: 'single_select' | 'multi_select'
  
  /** Available options */
  options: MCQOption[]
  
  /** Whether to allow free-text input */
  allow_free_text: boolean
  
  /** Placeholder for free-text input */
  free_text_placeholder: string
  
  /** Whether this category is required */
  required?: boolean
  
  /** Help text or description */
  help_text?: string
  
  /** Default selected option IDs */
  defaults?: string[]
}

/**
 * Complete MCQ template for a design type.
 */
export interface MCQTemplate {
  /** Design type this template applies to */
  design_type: DesignType
  
  /** List of question categories */
  categories: MCQCategory[]
  
  /** Template version */
  version?: string
}

/**
 * User's answer to a single MCQ category.
 */
export interface MCQAnswer {
  /** Category ID */
  categoryId: string
  
  /** Selected option IDs */
  selectedIds: string[]
  
  /** Optional free-text addition */
  freeText?: string
  
  /** Timestamp when answered */
  answeredAt: number
}

/**
 * MCQ validation result.
 */
export interface MCQValidationResult {
  isValid: boolean
  errors: Array<{
    categoryId: string
    message: string
  }>
}


// ═══════════════════════════════════════════════════════════════════════════════
// 5. PHASE C — RETRIEVAL
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Retrieved reference design.
 */
export interface RetrievedDesign {
  /** Design identifier */
  id: string
  
  /** Design name */
  name: string
  
  /** Design type */
  type: DesignType
  
  /** Relevance score (0.0 to 1.0) */
  score: number
  
  /** Key components */
  components?: string[]
  
  /** Source/reference */
  source?: string
  
  /** Summary/description */
  summary?: string
}

/**
 * Retrieval response.
 */
export interface RetrievalResponse {
  designs: RetrievedDesign[]
  total_count: number
  query: string
}


// ═══════════════════════════════════════════════════════════════════════════════
// 6. PHASE D — GENERATION & SSE
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Section identifiers for generation pipeline.
 */
export type SectionId =
  | 'architecture'
  | 'capacity'
  | 'data_model'
  | 'api_design'
  | 'stack'

/**
 * Section generation status.
 */
export type SectionStatus =
  | 'pending'
  | 'started'
  | 'streaming'
  | 'complete'
  | 'error'
  | 'cancelled'

/**
 * Architecture component.
 */
export interface ArchComponent {
  /** Unique component identifier (snake_case) */
  id: string
  
  /** Human-readable name */
  name: string
  
  /** Component type */
  type:
    | 'client'
    | 'frontend'
    | 'gateway'
    | 'backend'
    | 'database'
    | 'queue'
    | 'cache'
    | 'cdn'
    | 'auth'
    | 'storage'
    | 'third_party'
    | 'external'
    | 'ai'
  
  /** Brief description */
  description: string
  
  /** List of responsibilities */
  responsibilities: string[]
  
  /** Connected component IDs */
  connections: string[]
  
  /** Specific named technology, e.g. "Redis 7", "PostgreSQL 15" */
  technology?: string

  /** Technology stack (legacy/alternate field — some sections use a list instead) */
  tech_stack?: string[]
  
  /** Scaling strategy */
  scaling?: string
}

/**
 * A directed data/event flow between two components.
 */
export interface ArchDataFlow {
  from: string
  to: string
  label?: string
  protocol?: string
}

/**
 * A deployment zone grouping a set of components (CDN / Edge / App Tier / etc).
 */
export interface ArchDeploymentZone {
  zone: string
  components: string[]
}

/**
 * Architecture diagram data.
 */
export interface ArchitectureData {
  components: ArchComponent[]

  /** Directed edges between components, with protocol/label */
  data_flows?: ArchDataFlow[]

  /** Logical deployment groupings (CDN, Edge, App Tier, Data Tier, External) */
  deployment_zones?: ArchDeploymentZone[]

  /** Key design decisions with rationale, in order */
  key_design_decisions?: string[]
  
  /** Optional diagram metadata */
  metadata?: {
    total_components: number
    total_connections: number
    diagram_type?: string
  }
}

/**
 * Capacity estimation data.
 */
export interface CapacityData {
  /** Daily active users */
  dau: number
  
  /** Peak read queries per second */
  peak_read_qps: number
  
  /** Peak write queries per second */
  peak_write_qps: number
  
  /** Daily storage requirement in GB */
  daily_storage_gb: number
  
  /** 5-year storage projection in TB */
  five_year_storage_tb: number
  
  /** Bandwidth requirement in Gbps */
  bandwidth_gbps: number
  
  /** Cache dataset size in GB */
  cache_dataset_gb: number
  
  /** Calculation formulas for transparency */
  formulas: Record<string, string>
  
  /** Assumptions used */
  assumptions?: string[]
}

/**
 * Data model column definition.
 */
export interface DataModelColumn {
  /** Column name */
  name: string
  
  /** Data type */
  type: string
  
  /** Whether this is the primary key */
  primary?: boolean
  
  /** Whether this column is indexed */
  indexed?: boolean
  
  /** Whether this column is nullable */
  nullable?: boolean
  
  /** Default value */
  default?: string
  
  /** Column description */
  description?: string
}

/**
 * Data model entity (table/collection).
 */
export interface DataModelEntity {
  /** Entity/table name */
  name: string
  
  /** Column definitions */
  columns: DataModelColumn[]
  
  /** Sharding key (if applicable) */
  sharding_key: string | null
  
  /** Access patterns */
  access_patterns: string[]
  
  /** Indexes */
  indexes?: Array<{
    name: string
    columns: string[]
    unique?: boolean
  }>
  
  /** Relationships */
  relationships?: Array<{
    target: string
    type: 'one_to_one' | 'one_to_many' | 'many_to_many'
    foreign_key?: string
  }>
}

/**
 * Data model design data.
 */
export interface DataModelData {
  /** Database type decision */
  decision: 'SQL' | 'NoSQL' | 'Hybrid'
  
  /** Rationale for the decision */
  rationale: string
  
  /** Entity definitions */
  entities: DataModelEntity[]
  
  /** Schema diagrams or additional notes */
  notes?: string
}

/**
 * API endpoint definition.
 */
export interface ApiEndpoint {
  /** HTTP method */
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  
  /** Endpoint path */
  path: string
  
  /** Description */
  description: string
  
  /** Query parameters */
  query_params?: Record<string, string>
  
  /** Request body schema */
  request_body?: Record<string, string>
  
  /** Response schema */
  response: Record<string, string>
  
  /** Rate limit */
  rate_limit?: string
  
  /** Authentication required */
  auth_required?: boolean
  
  /** Example request */
  example_request?: string
  
  /** Example response */
  example_response?: string
}

/**
 * API design data.
 */
export interface ApiDesignData {
  /** API style */
  style: 'REST' | 'GraphQL' | 'gRPC' | 'WebSocket'
  
  /** Authentication method */
  auth: string
  
  /** Endpoint definitions */
  endpoints: ApiEndpoint[]
  
  /** Base URL */
  base_url?: string
  
  /** API version */
  version?: string
}

/**
 * Tech stack layer recommendation.
 */
export interface StackLayer {
  /** Layer name */
  layer:
    | 'database'
    | 'cache'
    | 'queue'
    | 'frontend'
    | 'backend'
    | 'cdn'
    | 'auth'
    | 'monitoring'
    | 'deployment'
    | 'ci_cd'
  
  /** Primary technology choice */
  primary: string
  
  /** Alternative technologies */
  alternatives: string[]
  
  /** Rationale for choice */
  rationale: string
  
  /** Trade-offs */
  trade_off: string
  
  /** Managed vs self-hosted */
  deployment_model?: 'managed' | 'self-hosted' | 'hybrid'
  
  /** Cost estimate */
  cost_estimate?: string
}

/**
 * Tech stack data.
 */
export interface StackData {
  layers: StackLayer[]
  
  /** Overall architecture philosophy */
  philosophy?: string
}

/**
 * Union of all section payload types.
 */
export type SectionPayload =
  | ArchitectureData
  | CapacityData
  | DataModelData
  | ApiDesignData
  | StackData

/**
 * Section generation result.
 */
export interface SectionResult {
  section: SectionId
  status: SectionStatus
  payload?: SectionPayload
  tokens_used?: number
  duration_ms?: number
  cached?: boolean
  error?: string
  started_at?: number
  completed_at?: number
}

/**
 * SSE event types (discriminated union).
 */
export type SSEEvent =
  | SSEPingEvent
  | SSEHeartbeatEvent
  | SSESectionStartEvent
  | SSESectionDoneEvent
  | SSESectionErrorEvent
  | SSEPipelineDoneEvent
  | SSEPipelineErrorEvent

/**
 * Base SSE event interface.
 */
interface SSEBaseEvent {
  type: string
  timestamp: number
  request_id?: string
}

/**
 * SSE ping event (connection established).
 */
export interface SSEPingEvent extends SSEBaseEvent {
  type: 'ping'
  session_id: string
  message: string
}

/**
 * SSE heartbeat event (keep-alive).
 */
export interface SSEHeartbeatEvent extends SSEBaseEvent {
  type: 'heartbeat'
}

/**
 * SSE section start event.
 */
export interface SSESectionStartEvent extends SSEBaseEvent {
  type: 'section.start'
  section: SectionId
  status: 'started'
}

/**
 * SSE section complete event.
 */
export interface SSESectionDoneEvent extends SSEBaseEvent {
  type: 'section.done'
  section: SectionId
  status: 'complete'
  payload: SectionPayload
  tokens_used: number
  duration_ms: number
  cached: boolean
}

/**
 * SSE section error event.
 */
export interface SSESectionErrorEvent extends SSEBaseEvent {
  type: 'section.error'
  section: SectionId
  status: 'error'
  error: string
  error_code?: string
}

/**
 * SSE pipeline complete event.
 */
export interface SSEPipelineDoneEvent extends SSEBaseEvent {
  type: 'pipeline.done'
  section: 'done'
  status: 'done'
  total_tokens?: number
  total_duration_ms?: number
}

/**
 * SSE pipeline error event.
 */
export interface SSEPipelineErrorEvent extends SSEBaseEvent {
  type: 'pipeline.error'
  error: string
  error_code: string
}

/**
 * SSE event handler callbacks.
 */
export interface SSEHandlers {
  onEvent: (event: SSEEvent) => void
  onDone: () => void
  onError: (error: string, errorCode?: string) => void
  onPing?: (event: SSEPingEvent) => void
  onHeartbeat?: (event: SSEHeartbeatEvent) => void
  onSectionStart?: (section: SectionId) => void
  onSectionDone?: (section: SectionId, payload: SectionPayload) => void
  onSectionError?: (section: SectionId, error: string) => void
}


// ═══════════════════════════════════════════════════════════════════════════════
// 7. ARTIFACT TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Artifact panel tab identifiers.
 */
export type ArtifactTab =
  | 'diagram'
  | 'capacity'
  | 'data_model'
  | 'api'
  | 'stack'

/**
 * Artifact panel state.
 */
export interface ArtifactState {
  /** Currently active tab */
  activeTab: ArtifactTab
  
  /** Whether the artifact panel is visible */
  isVisible: boolean
  
  /** Architecture diagram data */
  diagram?: ArchitectureData
  
  /** Capacity estimation data */
  capacity?: CapacityData
  
  /** Data model data */
  data_model?: DataModelData
  
  /** API design data */
  api?: ApiDesignData
  
  /** Tech stack data */
  stack?: StackData
  
  /** Loading state per section */
  loading?: Partial<Record<ArtifactTab, boolean>>
  
  /** Error state per section */
  errors?: Partial<Record<ArtifactTab, string>>
}

/**
 * Artifact tab metadata.
 */
export interface ArtifactTabMeta {
  id: ArtifactTab
  label: string
  icon: string
  section: SectionId | null
  description: string
}


// ═══════════════════════════════════════════════════════════════════════════════
// 8. CHAT & MESSAGE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Message sender role.
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * Message content type.
 */
export type MessageType =
  | 'text'
  | 'classification'
  | 'mcq'
  | 'status'
  | 'error'
  | 'retrieval'
  | 'generation'

/**
 * Chat message metadata.
 */
export interface ChatMessageMetadata {
  /** Classification result (for classification messages) */
  classification?: ClassifyResponse
  
  /** MCQ category (for MCQ messages) */
  mcqCategory?: MCQCategory
  
  /** MCQ category index */
  mcqCategoryIndex?: number
  
  /** Section ID (for status/generation messages) */
  section?: SectionId
  
  /** Section status */
  sectionStatus?: SectionStatus
  
  /** Retrieved designs (for retrieval messages) */
  retrievedDesigns?: RetrievedDesign[]
  
  /** Generation result (for generation messages) */
  generationResult?: SectionResult
  
  /** Timestamps */
  startedAt?: number
  completedAt?: number
  
  /** Additional custom metadata */
  [key: string]: any
}

/**
 * Chat message.
 */
export interface ChatMessage {
  /** Unique message ID */
  id: string
  
  /** Sender role */
  role: MessageRole
  
  /** Message type */
  type: MessageType
  
  /** Message content (supports markdown) */
  content: string
  
  /** Optional metadata */
  metadata?: ChatMessageMetadata
  
  /** Creation timestamp */
  createdAt: number
  
  /** Whether message is being edited */
  isEditing?: boolean
  
  /** Reactions (for future use) */
  reactions?: Array<{
    emoji: string
    count: number
  }>
}

/**
 * Chat input state.
 */
export interface ChatInputState {
  value: string
  isLoading: boolean
  isDisabled: boolean
  placeholder: string
}


// ═══════════════════════════════════════════════════════════════════════════════
// 9. API TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generic API response wrapper.
 */
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: ApiError
  metadata?: {
    request_id: string
    timestamp: number
    duration_ms?: number
  }
}

/**
 * API error structure.
 */
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  field?: string
}

/**
 * Create session request payload.
 */
export interface CreateSessionPayload {
  prompt: string
  design_type: DesignType
  context: SessionContext
}

/**
 * Create session response.
 */
export interface CreateSessionResponse {
  session_id: string
  retrieve_url: string
  stream_url: string
  status: SessionStatus
  created_at: number
}

/**
 * Get session response.
 */
export interface GetSessionResponse {
  session_id: string
  status: SessionStatus
  design_type: DesignType
  context: SessionContext
  sections: Partial<Record<SectionId, SectionResult>>
  created_at: number
  completed_at?: number
  total_tokens?: number
  total_duration_ms?: number
}

/**
 * Generation status response.
 */
export interface GenerationStatusResponse {
  session_id: string
  session_status: SessionStatus
  sections: Record<SectionId, {
    status: SectionStatus
    tokens_used?: number
    duration_ms?: number
    cached?: boolean
  }>
  total_tokens: number
  total_duration_ms: number
}

/**
 * API client configuration.
 */
export interface ApiConfig {
  baseUrl: string
  timeout: number
  retries: number
  headers?: Record<string, string>
}


// ═══════════════════════════════════════════════════════════════════════════════
// 10. COMPONENT PROP TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Chat message component props.
 */
export interface ChatMessageProps {
  message: ChatMessage
  mcqTemplate?: MCQTemplate
  onMcqAnswer?: (categoryId: string, selectedIds: string[], freeText?: string) => void
  onMcqNext?: () => void
  onRetry?: () => void
}

/**
 * Artifact panel component props.
 */
export interface ArtifactPanelProps {
  artifact: ArtifactState
  onTabChange: (tab: ArtifactTab) => void
  onClose?: () => void
}

/**
 * MCQ chip group component props.
 */
export interface MCQChipGroupProps {
  category: MCQCategory
  selectedIds: string[]
  freeText?: string
  onSelect: (selectedIds: string[], freeText?: string) => void
  disabled?: boolean
}

/**
 * Sidebar component props.
 */
export interface SidebarProps {
  sessions: SessionHistoryItem[]
  activeSessionId?: string
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onDeleteSession?: (id: string) => void
}

/**
 * Button component props.
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

/**
 * Input component props.
 */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

/**
 * Modal component props.
 */
export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'full'
  closeOnOverlayClick?: boolean
}


// ═══════════════════════════════════════════════════════════════════════════════
// 11. STORE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Zustand store state interface.
 */
export interface StoreState {
  // Session history
  sessionHistory: SessionHistoryItem[]
  
  // Active session
  session: Session
  messages: ChatMessage[]
  artifact: ArtifactState
  
  // Session flow actions
  startSession: (prompt: string) => void
  setClassification: (result: ClassifyResponse) => void
  setDesignType: (type: DesignType) => void
  setMcqTemplate: (template: MCQTemplate) => void
  answerMcqCategory: (categoryId: string, selectedIds: string[], freeText?: string) => void
  nextMcqCategory: () => void
  setSessionStatus: (status: SessionStatus) => void
  setSessionId: (id: string) => void
  resetSession: () => void
  
  // Message actions
  addMessage: (
    role: MessageRole,
    type: MessageType,
    content: string,
    metadata?: ChatMessageMetadata
  ) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  deleteMessage: (id: string) => void
  
  // Artifact actions
  setArtifactVisible: (visible: boolean) => void
  setArtifactTab: (tab: ArtifactTab) => void
  setArtifactSection: (section: string, data: SectionPayload) => void
  setArtifactLoading: (section: ArtifactTab, loading: boolean) => void
  setArtifactError: (section: ArtifactTab, error: string | null) => void
  
  // Phase D streaming actions
  handleSSEEvent: (event: SSEEvent) => void
  handleStreamDone: () => void
  handleStreamError: (error: string, errorCode?: string) => void
}


// ═══════════════════════════════════════════════════════════════════════════════
// 12. CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Design type constants.
 */
export const DESIGN_TYPES = {
  HLD: 'HLD' as const,
  LLD: 'LLD' as const,
} as const

/**
 * Session status constants.
 */
export const SESSION_STATUS = {
  IDLE: 'idle' as const,
  CLASSIFYING: 'classifying' as const,
  MCQ: 'mcq' as const,
  CREATING: 'creating' as const,
  RETRIEVING: 'retrieving' as const,
  GENERATING: 'generating' as const,
  COMPLETE: 'complete' as const,
  ERROR: 'error' as const,
} as const

/**
 * Section ID constants.
 */
export const SECTIONS = {
  ARCHITECTURE: 'architecture' as const,
  CAPACITY: 'capacity' as const,
  DATA_MODEL: 'data_model' as const,
  API_DESIGN: 'api_design' as const,
  STACK: 'stack' as const,
} as const

/**
 * Artifact tab constants.
 */
export const ARTIFACT_TABS = {
  DIAGRAM: 'diagram' as const,
  CAPACITY: 'capacity' as const,
  DATA_MODEL: 'data_model' as const,
  API: 'api' as const,
  STACK: 'stack' as const,
} as const

/**
 * Artifact tab metadata.
 */
export const ARTIFACT_TAB_META: ArtifactTabMeta[] = [
  {
    id: 'diagram',
    label: 'Diagram',
    icon: 'workflow',
    section: 'architecture',
    description: 'System architecture and component diagram',
  },
  {
    id: 'capacity',
    label: 'Capacity',
    icon: 'zap',
    section: 'capacity',
    description: 'Capacity estimation and scaling calculations',
  },
  {
    id: 'data_model',
    label: 'Data Model',
    icon: 'database',
    section: 'data_model',
    description: 'Database schema and data model design',
  },
  {
    id: 'api',
    label: 'API',
    icon: 'arrow-left-right',
    section: 'api_design',
    description: 'API endpoints and interface design',
  },
  {
    id: 'stack',
    label: 'Stack',
    icon: 'layers',
    section: 'stack',
    description: 'Technology stack recommendations',
  },
] as const

/**
 * Section display names.
 */
export const SECTION_NAMES: Record<SectionId, string> = {
  architecture: 'Architecture Diagram',
  capacity: 'Capacity Estimation',
  data_model: 'Data Model',
  api_design: 'API Design',
  stack: 'Tech Stack',
} as const

/**
 * Component type colors.
 */
export const COMPONENT_COLORS: Record<ArchComponent['type'], string> = {
  client: 'bg-blue-500',
  frontend: 'bg-blue-500',
  gateway: 'bg-teal-500',
  backend: 'bg-cyan-500',
  database: 'bg-yellow-500',
  queue: 'bg-purple-500',
  cache: 'bg-green-500',
  cdn: 'bg-gray-500',
  auth: 'bg-orange-500',
  storage: 'bg-pink-500',
  third_party: 'bg-indigo-500',
  external: 'bg-indigo-500',
  ai: 'bg-red-500',
} as const

/**
 * API endpoint paths.
 */
export const API_ENDPOINTS = {
  CLASSIFY: '/api/classify',
  MCQ_TEMPLATE: (type: DesignType) => `/api/mcq/${type.toLowerCase()}`,
  CREATE_SESSION: '/api/sessions',
  GET_SESSION: (id: string) => `/api/sessions/${id}`,
  STREAM_SESSION: (id: string) => `/api/sessions/${id}/stream`,
  GENERATION_STATUS: (id: string) => `/api/sessions/${id}/generation/status`,
  CANCEL_GENERATION: (id: string) => `/api/sessions/${id}/generation/cancel`,
} as const

/**
 * Local storage keys.
 */
export const STORAGE_KEYS = {
  SESSION_HISTORY: 'sysdesign_session_history',
  USER_PREFERENCES: 'sysdesign_user_preferences',
  THEME: 'sysdesign_theme',
} as const

/**
 * Error codes.
 */
export const ERROR_CODES = {
  SESSION_NOT_FOUND: "SESSION_NOT_FOUND" as const,
  INVALID_STATE: "INVALID_SESSION_STATE" as const,
  SESSION_EXPIRED: "SESSION_EXPIRED" as const,
  CONCURRENT_GENERATION: "CONCURRENT_GENERATION" as const,
  GENERATION_FAILED: "GENERATION_FAILED" as const,
  CLIENT_DISCONNECT: "CLIENT_DISCONNECT" as const,
  DATABASE_ERROR: "DATABASE_ERROR" as const,
  NETWORK_ERROR: "NETWORK_ERROR" as const,
  TIMEOUT: "TIMEOUT" as const,
  VALIDATION_ERROR: "VALIDATION_ERROR" as const,
  INTERNAL: "INTERNAL_ERROR" as const,  // ← ADD THIS LINE
} as const
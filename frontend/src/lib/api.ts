/**
 * SysDesign AI — API Client
 * =========================
 * 
 * Centralized API client for all backend communication.
 * Handles REST endpoints and SSE streaming with proper error handling.
 * 
 * Features:
 *   - Type-safe API calls with generics
 *   - SSE streaming with event parsing
 *   - Automatic retry with exponential backoff
 *   - Request timeout handling
 *   - Structured error responses
 *   - Request ID tracking for debugging
 * 
 * @version 3.0.0
 * @author SysDesign AI
 */

import type {
  // Phase A
  ClassifyResponse,
  ClassifyRequest,
  
  // Phase B
  MCQTemplate,
  DesignType,
  
  // Session
  CreateSessionPayload,
  CreateSessionResponse,
  GetSessionResponse,
  GenerationStatusResponse,
  
  // SSE
  SSEEvent,
  SSEHandlers,
  
  // API types
  ApiResponse,
  ApiError,
  ApiConfig,
} from "@/types"

import { API_ENDPOINTS, ERROR_CODES } from "@/types"

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30000, // 30 seconds
  retries: 3,
  headers: {
    "Content-Type": "application/json",
  },
}

let config: ApiConfig = { ...DEFAULT_CONFIG }

/**
 * Configure the API client.
 */
export function configureApi(overrides: Partial<ApiConfig>): void {
  config = { ...config, ...overrides }
}

/**
 * Reset to default configuration.
 */
export function resetApiConfig(): void {
  config = { ...DEFAULT_CONFIG }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ERROR HANDLING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Custom API error class with structured error information.
 */
export class ApiClientError extends Error {
  public readonly code: string
  public readonly status: number
  public readonly details?: Record<string, any>
  public readonly requestId?: string

  constructor(
    message: string,
    code: string = ERROR_CODES.INTERNAL,
    status: number = 500,
    details?: Record<string, any>,
    requestId?: string,
  ) {
    super(message)
    this.name = "ApiClientError"
    this.code = code
    this.status = status
    this.details = details
    this.requestId = requestId

    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiClientError)
    }
  }

  /**
   * Create a user-friendly error message.
   */
  toUserMessage(): string {
    switch (this.code) {
      case ERROR_CODES.SESSION_NOT_FOUND:
        return "Session not found. It may have expired or been deleted."
      case ERROR_CODES.INVALID_STATE:
        return "Session is in an invalid state for this operation."
      case ERROR_CODES.SESSION_EXPIRED:
        return "Session has expired. Please start a new session."
      case ERROR_CODES.CONCURRENT_GENERATION:
        return "Generation is already in progress for this session."
      case ERROR_CODES.GENERATION_FAILED:
        return "Failed to generate design. Please try again."
      case ERROR_CODES.CLIENT_DISCONNECT:
        return "Connection was interrupted. Please try again."
      case ERROR_CODES.DATABASE_ERROR:
        return "Database error occurred. Please try again later."
      case ERROR_CODES.NETWORK_ERROR:
        return "Network error. Please check your connection."
      case ERROR_CODES.TIMEOUT:
        return "Request timed out. Please try again."
      case ERROR_CODES.VALIDATION_ERROR:
        return "Invalid input. Please check your data."
      default:
        return this.message
    }
  }
}

/**
 * Parse error response from backend.
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json()
    return {
      code: data.error_code || data.code || ERROR_CODES.INTERNAL,
      message: data.detail || data.error || data.message || response.statusText,
      details: data.details,
    }
  } catch {
    return {
      code: ERROR_CODES.INTERNAL,
      message: response.statusText || "Unknown error",
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// HTTP CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Make an HTTP request with timeout and retry logic.
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
  attempt: number = 1,
): Promise<T> {
  const url = `${config.baseUrl}${path}`
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), config.timeout)

  const requestId = generateRequestId()

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...config.headers,
        ...options.headers,
        "X-Request-ID": requestId,
      },
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const error = await parseErrorResponse(response)
      throw new ApiClientError(
        error.message,
        error.code,
        response.status,
        error.details,
        requestId,
      )
    }

    const data = await response.json()
    return data as T
  } catch (err) {
    clearTimeout(timeoutId)

    // Handle abort/timeout
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiClientError(
        "Request timed out",
        ERROR_CODES.TIMEOUT,
        408,
        undefined,
        requestId,
      )
    }

    // Handle network errors
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new ApiClientError(
        "Network error",
        ERROR_CODES.NETWORK_ERROR,
        0,
        undefined,
        requestId,
      )
    }

    // Retry logic for transient errors
    if (attempt < config.retries && isRetryableError(err)) {
      const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000)
      await sleep(delay)
      return request<T>(path, options, attempt + 1)
    }

    // Re-throw ApiClientError
    if (err instanceof ApiClientError) {
      throw err
    }

    // Wrap unknown errors
    throw new ApiClientError(
      err instanceof Error ? err.message : "Unknown error",
      ERROR_CODES.INTERNAL,
      500,
      undefined,
      requestId,
    )
  }
}

/**
 * Check if an error is retryable.
 */
function isRetryableError(err: unknown): boolean {
  if (err instanceof ApiClientError) {
    // Retry on 5xx errors, network errors, and timeouts
    return err.status >= 500 || err.status === 0 || err.code === ERROR_CODES.TIMEOUT
  }
  return false
}

/**
 * Sleep for a given number of milliseconds.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Generate a unique request ID.
 */
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE A — CLASSIFICATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Classify a design prompt as HLD or LLD.
 */
export async function classifyPrompt(prompt: string): Promise<ClassifyResponse> {
  return request<ClassifyResponse>(API_ENDPOINTS.CLASSIFY, {
    method: "POST",
    body: JSON.stringify({ prompt } satisfies ClassifyRequest),
  })
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE B — MCQ
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch MCQ template for a design type.
 */
export async function getMCQTemplate(designType: DesignType): Promise<MCQTemplate> {
  return request<MCQTemplate>(API_ENDPOINTS.MCQ_TEMPLATE(designType))
}

// ═══════════════════════════════════════════════════════════════════════════════
// SESSION MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create a new design session.
 */
export async function createSession(
  payload: CreateSessionPayload,
): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>(API_ENDPOINTS.CREATE_SESSION, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

/**
 * Get session details and generation results.
 */
export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  return request<GetSessionResponse>(API_ENDPOINTS.GET_SESSION(sessionId))
}

/**
 * Get generation status for a session.
 */
export async function getGenerationStatus(
  sessionId: string,
): Promise<GenerationStatusResponse> {
  return request<GenerationStatusResponse>(
    API_ENDPOINTS.GENERATION_STATUS(sessionId),
  )
}

/**
 * Cancel an in-progress generation.
 */
export async function cancelGeneration(sessionId: string): Promise<void> {
  await request<void>(API_ENDPOINTS.CANCEL_GENERATION(sessionId), {
    method: "POST",
  })
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE D — SSE STREAMING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * SSE connection state.
 */
interface SSEConnection {
  eventSource: EventSource
  cleanup: () => void
  isConnected: boolean
}

/**
 * Parse SSE event from raw text.
 * 
 * SSE format:
 *   id: <event_id>
 *   event: <event_type>
 *   data: <json>
 *   \n
 */
function parseSSEEvent(raw: string): SSEEvent | null {
  const lines = raw.split("\n")
  let eventType = "message"
  let data = ""

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim()
    } else if (line.startsWith("data:")) {
      data += line.slice(5).trim()
    }
  }

  if (!data) return null

  try {
    const parsed = JSON.parse(data)
    return {
      ...parsed,
      type: eventType,
    } as SSEEvent
  } catch (err) {
    console.error("Failed to parse SSE event:", err, raw)
    return null
  }
}

/**
 * Open an SSE stream for generation events.
 * 
 * @param sessionId - Session ID to stream
 * @param handlers - Event handler callbacks
 * @returns Cleanup function to close the connection
 */
export function openStream(
  sessionId: string,
  handlers: SSEHandlers,
): () => void {
  const url = `${config.baseUrl}${API_ENDPOINTS.STREAM_SESSION(sessionId)}`
  
  // Use fetch with ReadableStream for better control
  const controller = new AbortController()
  let isClosed = false

  const connect = async () => {
    try {
      const response = await fetch(url, {
        headers: {
          Accept: "text/event-stream",
          "Cache-Control": "no-cache",
        },
        signal: controller.signal,
      })

      if (!response.ok) {
        const error = await parseErrorResponse(response)
        handlers.onError(error.message, error.code)
        return
      }

      if (!response.body) {
        handlers.onError("No response body", ERROR_CODES.INTERNAL)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          // Stream ended normally
          handlers.onDone()
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Process complete events (separated by double newline)
        const events = buffer.split("\n\n")
        buffer = events.pop() || "" // Keep incomplete event in buffer

        for (const eventText of events) {
          if (!eventText.trim()) continue

          const event = parseSSEEvent(eventText)
          if (!event) continue

          // Route to appropriate handler
          handlers.onEvent(event)

          switch (event.type) {
            case "ping":
              handlers.onPing?.(event)
              break
            case "heartbeat":
              handlers.onHeartbeat?.(event)
              break
            case "section.start":
              handlers.onSectionStart?.(event.section)
              break
            case "section.done":
              handlers.onSectionDone?.(event.section, event.payload)
              break
            case "section.error":
              handlers.onSectionError?.(event.section, event.error)
              break
            case "pipeline.done":
              handlers.onDone()
              isClosed = true
              break
            case "pipeline.error":
              handlers.onError(event.error, event.error_code)
              isClosed = true
              break
          }

          if (isClosed) break
        }

        if (isClosed) break
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // Connection was intentionally closed
        return
      }

      const message = err instanceof Error ? err.message : "Unknown error"
      handlers.onError(message, ERROR_CODES.NETWORK_ERROR)
    }
  }

  // Start connection
  connect()

  // Return cleanup function
  return () => {
    if (!isClosed) {
      isClosed = true
      controller.abort()
    }
  }
}

/**
 * Legacy SSE connection using EventSource (simpler but less control).
 * 
 * @deprecated Use `openStream` instead for better error handling
 */
export function openStreamLegacy(
  sessionId: string,
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
  onError: (err: string) => void,
): () => void {
  const url = `${config.baseUrl}${API_ENDPOINTS.STREAM_SESSION(sessionId)}`
  const es = new EventSource(url)

  es.onmessage = (e) => {
    try {
      const data: SSEEvent = JSON.parse(e.data)
      
      if (data.type === "pipeline.done") {
        onDone()
        es.close()
      } else if (data.type === "pipeline.error") {
        onError(data.error || "Unknown error")
        es.close()
      } else {
        onEvent(data)
      }
    } catch {
      onError("Failed to parse stream event")
    }
  }

  es.onerror = () => {
    onError("SSE connection error")
    es.close()
  }

  return () => es.close()
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Check if the API is reachable.
 */
export async function healthCheck(): Promise<boolean> {
  try {
    await request<{ status: string }>("/health")
    return true
  } catch {
    return false
  }
}

/**
 * Get the current API configuration.
 */
export function getApiConfig(): Readonly<ApiConfig> {
  return { ...config }
}

/**
 * Build a full URL for an endpoint.
 */
export function buildUrl(path: string): string {
  return `${config.baseUrl}${path}`
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════════

export {
  // Re-export types for convenience
  type ApiResponse,
  type ApiError,
  type ApiConfig,
}

// Default export for convenience
export default {
  configure: configureApi,
  resetConfig: resetApiConfig,
  getConfig: getApiConfig,
  healthCheck,
  buildUrl,
  
  // Phase A
  classifyPrompt,
  
  // Phase B
  getMCQTemplate,
  
  // Session
  createSession,
  getSession,
  getGenerationStatus,
  cancelGeneration,
  
  // Phase D
  openStream,
  openStreamLegacy,
}
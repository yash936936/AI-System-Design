import type {
  ClassifyResponse,
  ClassifyRequest,
  MCQTemplate,
  DesignType,
  CreateSessionPayload,
  CreateSessionResponse,
  GetSessionResponse,
  GenerationStatusResponse,
  SSEEvent,
  SSEHandlers,
  ApiResponse,
  ApiError,
  ApiConfig,
} from "@/types"

import { API_ENDPOINTS, ERROR_CODES } from "@/types"

const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30000,
  retries: 3,
  headers: { "Content-Type": "application/json" },
}

let config: ApiConfig = { ...DEFAULT_CONFIG }

export function configureApi(overrides: Partial<ApiConfig>): void {
  config = { ...config, ...overrides }
}

export function resetApiConfig(): void {
  config = { ...DEFAULT_CONFIG }
}

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
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiClientError)
    }
  }

  toUserMessage(): string {
    switch (this.code) {
      case ERROR_CODES.SESSION_NOT_FOUND: return "Session not found. It may have expired or been deleted."
      case ERROR_CODES.INVALID_STATE: return "Session is in an invalid state for this operation."
      case ERROR_CODES.SESSION_EXPIRED: return "Session has expired. Please start a new session."
      case ERROR_CODES.CONCURRENT_GENERATION: return "Generation is already in progress for this session."
      case ERROR_CODES.GENERATION_FAILED: return "Failed to generate design. Please try again."
      case ERROR_CODES.CLIENT_DISCONNECT: return "Connection was interrupted. Please try again."
      case ERROR_CODES.DATABASE_ERROR: return "Database error occurred. Please try again later."
      case ERROR_CODES.NETWORK_ERROR: return "Network error. Please check your connection."
      case ERROR_CODES.TIMEOUT: return "Request timed out. Please try again."
      case ERROR_CODES.VALIDATION_ERROR: return "Invalid input. Please check your data."
      default: return this.message
    }
  }
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json()
    return {
      code: data.error_code || data.code || ERROR_CODES.INTERNAL,
      message: data.detail || data.error || data.message || response.statusText,
      details: data.details,
    }
  } catch {
    return { code: ERROR_CODES.INTERNAL, message: response.statusText || "Unknown error" }
  }
}

function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function isRetryableError(err: unknown): boolean {
  if (err instanceof ApiClientError) {
    return err.status >= 500 || err.status === 0 || err.code === ERROR_CODES.TIMEOUT
  }
  return false
}

async function request<T>(path: string, options: RequestInit = {}, attempt: number = 1): Promise<T> {
  const url = `${config.baseUrl}${path}`
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), config.timeout)
  const requestId = generateRequestId()

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: { ...config.headers, ...options.headers, "X-Request-ID": requestId },
    })
    clearTimeout(timeoutId)

    if (!response.ok) {
      const error = await parseErrorResponse(response)
      throw new ApiClientError(error.message, error.code, response.status, error.details, requestId)
    }

    return (await response.json()) as T
  } catch (err) {
    clearTimeout(timeoutId)

    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiClientError("Request timed out", ERROR_CODES.TIMEOUT, 408, undefined, requestId)
    }
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new ApiClientError("Network error", ERROR_CODES.NETWORK_ERROR, 0, undefined, requestId)
    }
    if (attempt < config.retries && isRetryableError(err)) {
      await sleep(Math.min(1000 * Math.pow(2, attempt - 1), 10000))
      return request<T>(path, options, attempt + 1)
    }
    if (err instanceof ApiClientError) throw err
    throw new ApiClientError(
      err instanceof Error ? err.message : "Unknown error",
      ERROR_CODES.INTERNAL, 500, undefined, requestId,
    )
  }
}

export async function classifyPrompt(prompt: string): Promise<ClassifyResponse> {
  return request<ClassifyResponse>(API_ENDPOINTS.CLASSIFY, {
    method: "POST",
    body: JSON.stringify({ prompt } satisfies ClassifyRequest),
  })
}

export async function getMCQTemplate(designType: DesignType): Promise<MCQTemplate> {
  return request<MCQTemplate>(API_ENDPOINTS.MCQ_TEMPLATE(designType))
}

export async function createSession(payload: CreateSessionPayload): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>(API_ENDPOINTS.CREATE_SESSION, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  return request<GetSessionResponse>(API_ENDPOINTS.GET_SESSION(sessionId))
}

export async function getGenerationStatus(sessionId: string): Promise<GenerationStatusResponse> {
  return request<GenerationStatusResponse>(API_ENDPOINTS.GENERATION_STATUS(sessionId))
}

export async function cancelGeneration(sessionId: string): Promise<void> {
  await request<void>(API_ENDPOINTS.CANCEL_GENERATION(sessionId), { method: "POST" })
}

function parseSSEEvent(raw: string): SSEEvent | null {
  const lines = raw.split("\\n")
  let eventType = "message"
  let data = ""
  for (const line of lines) {
    if (line.startsWith("event:")) eventType = line.slice(6).trim()
    else if (line.startsWith("data:")) data += line.slice(5).trim()
  }
  if (!data) return null
  try {
    return { type: eventType, ...JSON.parse(data) } as SSEEvent
  } catch (err) {
    console.error("Failed to parse SSE event:", err, raw)
    return null
  }
}

export function openStream(sessionId: string, handlers: SSEHandlers): () => void {
  const url = `${config.baseUrl}${API_ENDPOINTS.STREAM_SESSION(sessionId)}`
  const controller = new AbortController()
  let isClosed = false

  const connect = async () => {
    try {
      const response = await fetch(url, {
        headers: { Accept: "text/event-stream", "Cache-Control": "no-cache" },
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
        if (done) { handlers.onDone(); break }
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split("\\n\\n")
        buffer = events.pop() || ""

        for (const eventText of events) {
          if (!eventText.trim()) continue
          const event = parseSSEEvent(eventText)
          if (!event) continue
          handlers.onEvent(event)
          switch (event.type) {
            case "ping": handlers.onPing?.(event); break
            case "heartbeat": handlers.onHeartbeat?.(event); break
            case "section.start": handlers.onSectionStart?.(event.section); break
            case "section.done": handlers.onSectionDone?.(event.section, event.payload); break
            case "section.error": handlers.onSectionError?.(event.section, event.error); break
            case "pipeline.done": handlers.onDone(); isClosed = true; break
            case "pipeline.error": handlers.onError(event.error, event.error_code); isClosed = true; break
          }
          if (isClosed) break
        }
        if (isClosed) break
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return
      handlers.onError(err instanceof Error ? err.message : "Unknown error", ERROR_CODES.NETWORK_ERROR)
    }
  }

  connect()
  return () => { if (!isClosed) { isClosed = true; controller.abort() } }
}

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
      if (data.type === "pipeline.done") { onDone(); es.close() }
      else if (data.type === "pipeline.error") { onError(data.error || "Unknown error"); es.close() }
      else onEvent(data)
    } catch { onError("Failed to parse stream event") }
  }
  es.onerror = () => { onError("SSE connection error"); es.close() }
  return () => es.close()
}

export async function healthCheck(): Promise<boolean> {
  try { await request<{ status: string }>("/health"); return true } catch { return false }
}

export function getApiConfig(): Readonly<ApiConfig> { return { ...config } }
export function buildUrl(path: string): string { return `${config.baseUrl}${path}` }

export { type ApiResponse, type ApiError, type ApiConfig }

export default {
  configure: configureApi,
  resetConfig: resetApiConfig,
  getConfig: getApiConfig,
  healthCheck,
  buildUrl,
  classifyPrompt,
  getMCQTemplate,
  createSession,
  getSession,
  getGenerationStatus,
  cancelGeneration,
  openStream,
  openStreamLegacy,
}

// Auth-aware helpers

let _cachedToken: string | null = null
let _tokenExpiry = 0

export async function refreshBackendToken(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/backend-token", { method: "POST" })
    if (!res.ok) return null
    const data = await res.json()
    _cachedToken = data.token
    _tokenExpiry = data.expiresAt
    return _cachedToken
  } catch { return null }
}

export async function getBackendToken(): Promise<string | null> {
  const nowSecs = Math.floor(Date.now() / 1000)
  if (_cachedToken && nowSecs < _tokenExpiry - 300) return _cachedToken
  return refreshBackendToken()
}

export async function authRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getBackendToken()
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> ?? {}) }
  if (token) headers["Authorization"] = `Bearer ${token}`
  return request<T>(path, { ...options, headers })
}

export interface ExportRequest {
  format: "md" | "json" | "pdf"
  sections?: string[]
}

export interface ExportResponse {
  id: string
  session_id: string
  format: string
  sections: string[] | null
  download_url: string
  expires_at: string
  created_at: string
}

export async function createExport(sessionId: string, req: ExportRequest): Promise<ExportResponse> {
  return authRequest<ExportResponse>(`/api/sessions/${sessionId}/export`, {
    method: "POST",
    body: JSON.stringify(req),
  })
}

export async function getExport(exportId: string): Promise<ExportResponse> {
  return authRequest<ExportResponse>(`/api/exports/${exportId}`)
}

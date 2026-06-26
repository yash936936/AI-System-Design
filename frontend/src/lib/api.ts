import type {
  ClassifyResponse, MCQTemplate,
  SessionContext, DesignType,
} from "@/types"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Phase A: Classify ─────────────────────────────────────────────────────────

export async function classifyPrompt(prompt: string): Promise<ClassifyResponse> {
  return request("/api/classify", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  })
}

// ── Phase B: MCQ ──────────────────────────────────────────────────────────────

export async function getMCQTemplate(designType: string): Promise<MCQTemplate> {
  return request(`/api/mcq/${designType.toLowerCase()}`)
}

// ── Session ───────────────────────────────────────────────────────────────────

export interface CreateSessionPayload {
  prompt: string
  design_type: DesignType
  context: SessionContext
}

export interface CreateSessionResult {
  session_id: string
  retrieve_url: string
  stream_url: string
  status: string
}

export async function createSession(payload: CreateSessionPayload): Promise<CreateSessionResult> {
  return request("/api/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function getSession(sessionId: string): Promise<Record<string, unknown>> {
  return request(`/api/sessions/${sessionId}`)
}

// ── SSE stream (Stage 4+) ─────────────────────────────────────────────────────

export function openStream(
  sessionId: string,
  onEvent: (event: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (err: string) => void,
): () => void {
  const es = new EventSource(`${BASE}/api/sessions/${sessionId}/stream`)

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.status === "done") {
        onDone()
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
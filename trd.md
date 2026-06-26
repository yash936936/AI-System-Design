# TRD — SysDesign AI (v2)

## System Architecture Layers

### Frontend — Next.js 14 (Vercel)

Three-panel Claude.ai-identical layout. All state lives in a Zustand store. SSE connection is held open during generation and feeds the artifact panel tabs progressively.

| Concern | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| UI layout | Three-panel shell: sidebar 260px / chat flex-grow / artifact 420px |
| Diagram rendering | React Flow (interactive) + Mermaid (fallback SVG) |
| State management | Zustand — session store, MCQ state, artifact tab state |
| Styling | Tailwind CSS — tokens match Claude.ai colour palette |
| MCQ chips | Custom chip component — multi-select, free-text field |
| Streaming display | `EventSource` API consuming SSE from backend |
| Export | html2canvas (diagram PNG) + jsPDF (PDF bundle) |
| Vector display | Sources tab renders chunk cards with relevance score bar |

---

### Backend — FastAPI (Railway)

Python backend chosen over Node.js because the RAG stack (LangChain, ChromaDB, sentence-transformers) has a vastly more mature Python ecosystem. FastAPI gives async support for SSE streaming.

| Concern | Technology |
|---|---|
| Runtime | Python 3.11 + FastAPI |
| Streaming | `StreamingResponse` with `text/event-stream` |
| RAG orchestration | LangChain (retrieval chain) |
| Embedding | Gemini `text-embedding-004` via `google-generativeai` SDK |
| Vector store | ChromaDB (local, persistent) — pgvector as production upgrade |
| LLM calls | `google-generativeai` SDK — `gemini-1.5-flash` model |
| Web search | SerpAPI or Tavily (fallback only) |
| Rate limit control | In-process semaphore (asyncio.Semaphore, max 14/min) |
| Session store | In-memory dict for dev; PostgreSQL for production |
| GitHub ingestion | PyGithub + custom chunker (512 tokens, 50 overlap) |

---

### AI / LLM Layer

Strictly Gemini only. No Anthropic, no OpenAI. All calls use `gemini-1.5-flash` for generation and `text-embedding-004` for embeddings. Both are on the free tier.

| Concern | Technology / Approach |
|---|---|
| Primary model | `gemini-1.5-flash` (free: 15 RPM, 1M TPM, 1500 RPD) |
| Embedding model | `text-embedding-004` (free: 100 RPD) |
| Output mode | JSON mode (`response_mime_type: "application/json"`) |
| Prompt versioning | Stored in `prompt-library.md` + loaded from `/prompts/*.txt` files |
| Response cache | Redis-backed, keyed on `sha256(model + prompt)`, TTL 24hr |
| Rate control | asyncio.Semaphore(14) per minute window |
| Cost monitoring | Log every call: model, tokens_in, tokens_out, cached (bool) |

---

### RAG / Knowledge Base Layer

| Concern | Technology |
|---|---|
| Vector store | ChromaDB (local persistent storage, `/data/chroma`) |
| Embedding dim | 768 (Gemini text-embedding-004) |
| Chunk size | 512 tokens, 50-token overlap |
| Similarity metric | Cosine similarity |
| Retrieval top-k | 5 chunks |
| Fallback threshold | 0.6 cosine similarity — below this triggers web search |
| Famous designs store | Separate ChromaDB collection `famous_designs` — pre-loaded at startup |
| GitHub ingestion | Runs as a one-time script + scheduled weekly refresh |
| Web search | Triggered on low confidence; results chunked and injected into prompt |

**Target GitHub repos for ingestion (launch):**
- `donnemartin/system-design-primer`
- `checkcheckzz/system-design-interview`
- `madd86/awesome-system-design`
- `codersguild/System-Design`
- `binhnguyennus/awesome-scalability`

---

### Data Persistence

| Concern | Technology |
|---|---|
| Primary DB | PostgreSQL (Supabase) |
| ORM | SQLAlchemy (async) |
| Object storage | Cloudflare R2 (stage payloads + exports) |
| Cache | Upstash Redis (response cache + rate limit counters) |
| Vector store | ChromaDB (local) → pgvector (production) |

---

## Core API Contracts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/classify` | Classify prompt as LLD or HLD. Returns `{ type, confidence, reasoning }` |
| `GET` | `/api/mcq/:design_type` | Returns the full MCQ question set for a design type as a JSON template |
| `POST` | `/api/sessions` | Create a session with context object (MCQ answers). Returns `session_id` |
| `GET` | `/api/sessions/:id/retrieve` | Trigger RAG retrieval. Returns retrieved chunks + sources |
| `GET` | `/api/sessions/:id/stream` | SSE stream — emits generation events for each of 5 output sections |
| `GET` | `/api/sessions/:id` | Retrieve full completed session |
| `POST` | `/api/sessions/:id/chat` | Follow-up question in session context. Streams response |
| `POST` | `/api/sessions/:id/export` | Generate export bundle. Returns signed R2 download URL |
| `GET` | `/api/famous/:system_name` | Retrieve a pre-loaded famous design by name |

---

## Database Schema — Key Tables

| Table | Key Columns | Notes |
|---|---|---|
| `users` | `id, email, plan, created_at` | Local record synced from auth provider |
| `sessions` | `id, user_id, prompt, design_type, context_json, status` | `context_json` stores the full MCQ output object |
| `rag_retrievals` | `session_id, query, chunks_json, max_score, used_web_fallback` | Stored for eval and cache warm-up |
| `generation_outputs` | `session_id, section, payload_url, tokens_used, cached, duration_ms` | One row per section (arch/capacity/data/api/stack) |
| `gemini_usage` | `date, model, calls, tokens_in, tokens_out, cached_calls` | Daily rollup for RPD monitoring |
| `famous_designs` | `id, system_name, canonical_json, diagram_json, last_updated` | Pre-loaded; updated manually or via script |
| `exports` | `id, session_id, format, download_url, expires_at` | Signed R2 URL, 24hr TTL |

---

## Security

| Concern | Approach |
|---|---|
| Auth | JWT (short-lived, 15min) via NextAuth.js; Google OAuth as primary provider |
| Gemini API key | Server-side only, stored in Railway env vault. Never exposed to client |
| Prompt injection | User input and LLM system prompt clearly delimited in every call. Input sanitised (strip control chars, cap at 2000 chars) |
| Rate limiting | Per-IP: 5 sessions/day (free), 50/day (pro). Token-bucket via Redis |
| Vector store | Read-only from API layer. Ingestion script runs in separate privileged process |
| R2 exports | Pre-signed URLs, 24hr TTL. Private bucket. No public object access |

---

## Performance & Scalability Targets

| SLO | Target | Mechanism |
|---|---|---|
| LLD/HLD classification | < 2s (P95) | Flash model + tiny prompt |
| First output token (artifact panel) | < 5s after MCQ complete | RAG pre-fetched during last MCQ turn |
| Full generation (5 sections) | < 30s (P90) | 3 batched Gemini calls, parallel where safe |
| Famous design retrieval | < 500ms | Name-match lookup → stored JSON, no LLM call |
| Gemini RPD usage | < 70% of 1500/day | Response cache + batching |
| Concurrent active sessions | 50 (free tier constraint) | Queue > 50 sessions with position indicator |

---

## Infrastructure & Deployment

| Layer | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Next.js 14, edge-deployed. Static assets on CDN. |
| Backend | Railway | Python + FastAPI container. ChromaDB persisted volume. |
| Database | Supabase | Postgres + PgBouncer pooler. |
| Vector store | ChromaDB on Railway volume | Upgrade to pgvector when > 1M chunks |
| Cache | Upstash Redis | Response cache + rate limit counters |
| Object storage | Cloudflare R2 | Export bundles + payload JSON |
| GitHub ingestion | Railway cron job | Runs weekly; re-embeds changed content only |
| Observability | Sentry (errors) + custom Gemini usage dashboard | Daily RPD chart to catch overuse early |
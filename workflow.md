# Workflow — SysDesign AI (v2)

## Overview

The pipeline has two pre-generation phases (classification + clarification) and one generation phase. The generation phase is RAG-augmented — it retrieves relevant knowledge before calling the LLM. This structure reduces wasted LLM calls, improves output quality, and keeps Gemini API usage within free-tier limits.

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────┐
│  Phase A — Intent Classification        │  ← 1 Gemini call
│  Detect: LLD or HLD                     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Phase B — MCQ Clarification (9 turns)  │  ← 0 Gemini calls (rule-based)
│  Collect: functional, NFR, capacity,    │
│  data model, API, arch, bottleneck,     │
│  scalability, trade-offs                │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Phase C — RAG Retrieval                │  ← 1 embedding call + vector search
│  Query: vector store with context obj   │
│  → top-k chunks (famous designs + repos)│
│  Fallback: web search if score < 0.6    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Phase D — Generation (5 sections)      │  ← 1–3 Gemini calls (batched)
│  D1. Architecture diagram JSON          │
│  D2. Capacity estimation table          │
│  D3. Data model + schema                │
│  D4. API design                         │
│  D5. Tech stack recommendation          │
└─────────────────────────────────────────┘
    │
    ▼
Stream to artifact panel tabs + chat narrative
```

---

## Phase A — Intent Classification

**Input:** Raw user prompt (string)
**Output:** `{ type: "HLD" | "LLD", confidence: number, reasoning: string }`
**Gemini calls:** 1 (uses `gemini-1.5-flash` — cheapest model)
**Latency target:** < 2s

**Classification signals:**
- HLD signals: "design X", "architecture of", "how does X work at scale", "system design for"
- LLD signals: "implement X", "design the data structure for", "how would you code", "low-level design of", "deep dive into"
- Ambiguous prompts default to HLD; correction chip shown regardless

**Cost strategy:** This call is < 100 tokens input + < 50 tokens output. At Gemini Flash pricing, essentially free. Result is cached for the session — never re-called.

---

## Phase B — MCQ Clarification

**Input:** Design type + user selections per turn
**Output:** `context_object` — a structured JSON built incrementally across 9 turns
**Gemini calls:** 0 — MCQ questions are hardcoded templates, not LLM-generated
**Latency:** Real-time (no API calls)

The MCQ question sets are static templates selected by design type (HLD vs LLD) and domain (social, fintech, ecommerce, etc. — inferred from Phase A). No LLM is called during this phase, which is critical for rate limit preservation.

**Context object structure after Phase B:**
```json
{
  "designType": "HLD",
  "systemName": "Twitter Timeline",
  "functionalReqs": ["post tweets", "follow users", "timeline feed", "notifications"],
  "outOfScope": ["DMs", "video"],
  "userActors": ["end user", "admin"],
  "readWriteRatio": "read-heavy",
  "scale": "100M+ users",
  "dau": "50M",
  "availability": "99.99%",
  "consistency": "eventual",
  "latencyTarget": "< 200ms timeline load",
  "requestSizeCategory": "< 1KB",
  "dataModelPreference": "NoSQL preferred",
  "apiStyle": "REST",
  "architectureApproach": "microservices",
  "bottleneckFocus": ["timeline fanout", "hot user problem"],
  "scalabilityPriority": "horizontal scale",
  "tradeOffPriority": "availability over consistency"
}
```

---

## Phase C — RAG Retrieval

**Input:** `context_object`
**Output:** Top-k document chunks (k=5) with relevance scores
**Gemini calls:** 1 embedding call (`text-embedding-004`) to embed the query
**Vector search:** ChromaDB or pgvector (cosine similarity)
**Latency target:** < 3s

**Query construction:** The context object is serialised into a retrieval query: `"HLD for Twitter Timeline — read-heavy, 50M DAU, 99.99% availability, eventual consistency, NoSQL, REST, microservices, timeline fanout bottleneck"`.

**Knowledge base contents:**
- GitHub system design repos (chunked at 512 tokens, 50-token overlap)
- Famous designs pre-loaded: Netflix, X, WhatsApp, Meta, Uber, YouTube, Airbnb (stored as structured docs with diagram JSON + narrative)

**Famous design fast path:** If the prompt exactly or closely matches a pre-loaded system name, a name-match lookup is attempted before vector search. If matched (score > 0.9), the stored design is returned directly — no embedding call needed.

**Web search fallback:** If max chunk similarity < 0.6, a web search is triggered using the query string. Results are chunked and included alongside RAG results. A "Searched the web" indicator is shown in the Sources tab.

---

## Phase D — Generation

**Input:** `context_object` + retrieved chunks (as `[CONTEXT]` block in prompt)
**Output:** 5 structured JSON sections streamed to artifact panel
**Gemini calls:** 1–3 (batched where possible)
**Model:** `gemini-1.5-flash` (free tier: 15 RPM, 1M TPM, 1500 RPD)
**Latency target:** < 30s total, first token < 5s

### D1 — Architecture Generation
Produces the component graph JSON. Components typed, named, connected. This is the most token-intensive call. Output fed directly to React Flow renderer.

### D2 — Capacity Estimation
Derived mathematically from the MCQ `dau`, `requestSizeCategory`, and `readWriteRatio` answers. The LLM validates and narrates the math — it does not invent the numbers. Reduces hallucination risk significantly.

### D3 — Data Model
Entity schemas, SQL vs NoSQL decision, sharding key, access patterns. Uses the `dataModelPreference` from MCQ as a strong prior.

### D4 — API Design
Key endpoints for the functional requirements selected in MCQ. REST, GraphQL, or gRPC based on `apiStyle` selection. Request/response shapes, pagination, auth strategy.

### D5 — Tech Stack
Layer-by-layer recommendation. Every choice references specific MCQ answers (e.g. "Given your 99.99% availability target, we recommend managed Postgres via Supabase over self-hosted"). No generic recommendations.

**Batching strategy:** D2 + D3 are batched into a single Gemini call (they share context and are small). D4 + D5 are batched into another. D1 is a solo call (largest output). Total: 3 Gemini calls for generation.

---

## API Cost Budget per Session

| Phase | Model | Input tokens | Output tokens | RPD impact |
|---|---|---|---|---|
| A — Classification | Flash | ~150 | ~50 | 1 |
| B — MCQ | None | 0 | 0 | 0 |
| C — Embedding | text-embedding-004 | ~200 | — | 1 |
| D1 — Architecture | Flash | ~1500 | ~800 | 1 |
| D2+D3 — Capacity+Data | Flash | ~1200 | ~600 | 1 |
| D4+D5 — API+Stack | Flash | ~1000 | ~500 | 1 |
| **Total per session** | | **~4050** | **~1950** | **5 RPD** |

Gemini Flash free tier: **1500 RPD** → supports **300 full sessions/day** before hitting the limit.

---

## Gemini Rate Limit Controls

| Control | Mechanism |
|---|---|
| Response caching | Cache D1–D5 outputs keyed on `hash(context_object)` — identical prompts never re-call the API |
| Prompt compression | Context object trimmed to essential fields before each call — no redundant keys |
| RPM throttle | In-process queue with max 14 concurrent Gemini calls/minute (leaving 1 RPM headroom) |
| Embedding cache | Query embeddings cached for 24 hours — repeated similar queries reuse stored vectors |
| Famous design fast path | Name-matched designs skip all LLM generation — 0 RPD cost |
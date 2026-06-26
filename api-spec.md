# API Specification — SysDesign AI (v2)

> Base URL: `https://api.sysdesign.ai/v1`
> All requests: `Content-Type: application/json`
> Authenticated routes: `Authorization: Bearer <jwt>`

---

## POST `/api/classify`
**Classify a prompt as LLD or HLD**
Auth: Not required

**Request**
```json
{ "prompt": "Design Twitter's timeline feed" }
```

**Response `200 OK`**
```json
{
  "type": "HLD",
  "confidence": 0.97,
  "reasoning": "Prompt uses 'design X' framing with a product name — canonical HLD signal.",
  "suggested_correction": "LLD"
}
```

**Errors:** `422` prompt < 5 chars · `429` rate limit

---

## GET `/api/mcq/:design_type`
**Fetch the MCQ question template for a design type**
Auth: Not required
`design_type`: `hld` or `lld`

**Response `200 OK`**
```json
{
  "design_type": "hld",
  "categories": [
    {
      "id": "functional",
      "label": "Functional Requirements",
      "question": "What are the core features you need?",
      "type": "multi_select",
      "options": [
        { "id": "post_content", "label": "Post content" },
        { "id": "follow_users", "label": "Follow users" },
        { "id": "timeline_feed", "label": "Timeline feed" },
        { "id": "notifications", "label": "Notifications" },
        { "id": "search", "label": "Search" }
      ],
      "allow_free_text": true,
      "free_text_placeholder": "Add your own feature..."
    },
    {
      "id": "nfr_scale",
      "label": "Non-Functional — Scale",
      "question": "Total user base?",
      "type": "single_select",
      "options": [
        { "id": "small", "label": "< 10K users" },
        { "id": "medium", "label": "10K–1M users" },
        { "id": "large", "label": "1M–100M users" },
        { "id": "xlarge", "label": "100M+ users" }
      ],
      "allow_free_text": false
    }
  ]
}
```

---

## POST `/api/sessions`
**Create a session from the completed context object**
Auth: Optional (unauthenticated = ephemeral 24hr session)

**Request**
```json
{
  "prompt": "Design Twitter's timeline feed",
  "design_type": "HLD",
  "context": {
    "systemName": "Twitter Timeline",
    "functionalReqs": ["post_content", "follow_users", "timeline_feed"],
    "outOfScope": ["dms", "video"],
    "scale": "xlarge",
    "dau": "50M",
    "readWriteRatio": "read_heavy",
    "availability": "99.99",
    "consistency": "eventual",
    "dataModelPreference": "nosql",
    "apiStyle": "rest",
    "architectureApproach": "microservices",
    "bottleneckFocus": ["timeline_fanout", "hot_user"],
    "tradeOffPriority": "availability_over_consistency"
  }
}
```

**Response `202 Accepted`**
```json
{
  "session_id": "sess_abc123",
  "retrieve_url": "/api/sessions/sess_abc123/retrieve",
  "stream_url": "/api/sessions/sess_abc123/stream",
  "status": "queued"
}
```

**Errors:** `422` missing required context fields · `429` daily session limit

---

## GET `/api/sessions/:id/retrieve`
**Trigger RAG retrieval for a session**
Auth: Optional

**Response `200 OK`**
```json
{
  "session_id": "sess_abc123",
  "query": "HLD Twitter Timeline read-heavy 50M DAU eventual consistency microservices fanout",
  "chunks": [
    {
      "id": "chunk_001",
      "source": "donnemartin/system-design-primer",
      "section": "Design a News Feed System",
      "text": "Fan-out on write pre-computes the feed for each follower at write time...",
      "score": 0.89
    },
    {
      "id": "chunk_002",
      "source": "famous_designs/twitter",
      "section": "Timeline Architecture (2022)",
      "text": "Twitter migrated from fan-out-on-write to a hybrid model...",
      "score": 0.84
    }
  ],
  "max_score": 0.89,
  "used_web_fallback": false,
  "famous_design_matched": "twitter"
}
```

---

## GET `/api/sessions/:id/stream`
**SSE stream — receive generation events per section**
Auth: Optional
`Content-Type: text/event-stream`

**Event shape**
```json
{
  "section": "architecture",
  "status": "started | streaming | complete | error",
  "payload": {},
  "tokens_used": 812,
  "cached": false,
  "duration_ms": 4200
}
```

**Section payloads**

`architecture` payload:
```json
{
  "components": [
    {
      "id": "timeline_service",
      "name": "Timeline Service",
      "type": "backend",
      "description": "Aggregates and serves pre-computed user feeds",
      "responsibilities": ["Read from Redis cache", "Fallback to DB on cache miss"],
      "connections": ["redis_cache", "post_db", "api_gateway"]
    }
  ]
}
```

`capacity` payload:
```json
{
  "dau": 50000000,
  "peak_read_qps": 57870,
  "peak_write_qps": 5787,
  "daily_storage_gb": 50,
  "five_year_storage_tb": 91,
  "bandwidth_gbps": 0.46,
  "cache_dataset_gb": 200,
  "formulas": {
    "peak_read_qps": "50M DAU × 100 reads/day × 1.2 peak factor / 86400s = 69,444 QPS"
  }
}
```

`data_model` payload:
```json
{
  "decision": "NoSQL",
  "rationale": "Timeline fan-out requires wide rows indexed by user_id + timestamp — Cassandra's partition model fits exactly.",
  "entities": [
    {
      "name": "tweets",
      "columns": [
        { "name": "tweet_id", "type": "UUID", "primary": true },
        { "name": "user_id", "type": "UUID", "indexed": true },
        { "name": "content", "type": "TEXT" },
        { "name": "created_at", "type": "TIMESTAMPTZ" }
      ],
      "sharding_key": "user_id",
      "access_patterns": ["get by tweet_id", "list by user_id ordered by created_at DESC"]
    }
  ]
}
```

`api_design` payload:
```json
{
  "style": "REST",
  "auth": "JWT Bearer",
  "endpoints": [
    {
      "method": "GET",
      "path": "/v1/timeline",
      "description": "Fetch paginated timeline for authenticated user",
      "query_params": { "cursor": "string", "limit": "int (max 50)" },
      "response": { "tweets": "Tweet[]", "next_cursor": "string" },
      "rate_limit": "100 req/min per user"
    }
  ]
}
```

`stack` payload:
```json
{
  "layers": [
    {
      "layer": "database",
      "primary": "Apache Cassandra",
      "alternatives": ["DynamoDB", "ScyllaDB"],
      "rationale": "Given your 100M+ scale and read-heavy fan-out pattern, Cassandra's wide-column model provides O(1) timeline reads with tunable consistency.",
      "trade_off": "DynamoDB would reduce operational burden but increases cost at this data volume."
    }
  ]
}
```

**Terminal event:**
```json
{ "status": "done", "session_id": "sess_abc123", "total_tokens": 1950, "total_ms": 28400, "gemini_calls": 3, "cached": false }
```

---

## POST `/api/sessions/:id/chat`
**Follow-up question within session context**
Auth: Optional
Protocol: `text/event-stream`

**Request**
```json
{
  "message": "Why Cassandra over DynamoDB here?",
  "focus_section": "stack"
}
```

Streams response tokens. Terminal event: `{ "status": "done", "tokens_used": 310 }`

**Errors:** `429` — 10 follow-ups/session (free), unlimited (pro)

---

## GET `/api/famous/:system_name`
**Retrieve a pre-loaded famous design**
Auth: Not required
`system_name`: `netflix` | `twitter` | `whatsapp` | `meta` | `uber` | `youtube` | `airbnb`

**Response `200 OK`**
```json
{
  "system": "netflix",
  "title": "Netflix — Video Streaming Architecture",
  "last_updated": "2024-01",
  "diagram": { "components": [] },
  "sections": {
    "capacity": {},
    "data_model": {},
    "api_design": {},
    "stack": {}
  },
  "key_insights": [
    "Open Connect CDN — Netflix-owned ISP-embedded appliances reduce backbone traffic by 95%",
    "Chaos Engineering (Chaos Monkey) — deliberately kill production instances to test resilience",
    "Microservices: 700+ services, each deployed independently via Spinnaker"
  ],
  "sources": ["https://netflixtechblog.com/..."]
}
```

---

## POST `/api/sessions/:id/export`
**Generate export bundle**
Auth: Optional

**Request**
```json
{ "format": "pdf" | "markdown" | "json", "sections": ["architecture", "capacity", "data_model", "api_design", "stack"] }
```

**Response `200 OK`**
```json
{
  "export_id": "exp_xyz",
  "format": "pdf",
  "download_url": "https://r2.sysdesign.ai/exports/exp_xyz.pdf?token=...",
  "expires_at": "2024-01-16T10:30:00Z",
  "size_bytes": 310000
}
```